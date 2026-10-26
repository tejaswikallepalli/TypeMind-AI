"""C and C++ language adapters using GCC, Clang, or MSVC syntax/type checkers."""

from __future__ import annotations
import logging
import os
import re
import shutil
import tempfile
import time
import uuid
from typing import Dict, List, Optional, Tuple

from app.languages.base import BaseLanguageAdapter, safe_subprocess_run
from app.schemas.analysis import AnalysisResponse, AnalysisSummary
from app.schemas.common import ErrorCategory, FindingOrigin, Severity, SourceLocation, TypeInfo
from app.schemas.diagnostics import DiagnosticFinding
from app.schemas.languages import LanguageSupportLevel

logger = logging.getLogger("typemind.languages.c_cpp")

# Pattern: filename.c:12:5: error/warning: message
GCC_CLANG_REGEX = re.compile(
    r"^.*?:(?P<line>\d+):(?P<col>\d+):\s*(?P<severity>error|warning|fatal error):\s*(?P<msg>.*)$"
)
# MSVC pattern: filename.c(12): error C2065: message
MSVC_REGEX = re.compile(
    r"^.*?\((?P<line>\d+)\):\s*(?P<severity>error|warning)\s+(?P<code>C\d+):\s*(?P<msg>.*)$"
)


def find_c_compiler() -> Optional[Tuple[str, str]]:
    """Locate available C compiler: returns (binary_path, compiler_type)."""
    for comp in ["gcc", "clang"]:
        p = shutil.which(comp)
        if p:
            return p, "gnu"
    cl_p = shutil.which("cl")
    if cl_p:
        return cl_p, "msvc"
    return None


def find_cpp_compiler() -> Optional[Tuple[str, str]]:
    """Locate available C++ compiler: returns (binary_path, compiler_type)."""
    for comp in ["g++", "clang++"]:
        p = shutil.which(comp)
        if p:
            return p, "gnu"
    cl_p = shutil.which("cl")
    if cl_p:
        return cl_p, "msvc"
    return None


def _parse_c_cpp_diagnostics(
    output_text: str,
    file_path: Optional[str],
    lang_code: str,
    default_ext: str,
) -> Tuple[List[DiagnosticFinding], Optional[DiagnosticFinding]]:
    """Parse compiler diagnostics from GCC/Clang/MSVC stderr."""
    findings: List[DiagnosticFinding] = []
    syntax_error_finding: Optional[DiagnosticFinding] = None

    for line in output_text.splitlines():
        line_str = line.strip()
        if not line_str:
            continue

        match_gnu = GCC_CLANG_REGEX.match(line_str)
        if match_gnu:
            line_num = int(match_gnu.group("line"))
            col_num = int(match_gnu.group("col"))
            sev_str = match_gnu.group("severity").lower()
            msg_str = match_gnu.group("msg").strip()
            code_id = f"TM_{lang_code.upper()}_ERR"
        else:
            match_msvc = MSVC_REGEX.match(line_str)
            if match_msvc:
                line_num = int(match_msvc.group("line"))
                col_num = 1
                sev_str = match_msvc.group("severity").lower()
                code_id = match_msvc.group("code")
                msg_str = match_msvc.group("msg").strip()
            else:
                continue

        severity = Severity.ERROR if "error" in sev_str else Severity.WARNING

        category = ErrorCategory.TYPE_MISMATCH
        msg_lower = msg_str.lower()
        if "incompatible type" in msg_lower or "cannot convert" in msg_lower or "assignment to" in msg_lower:
            category = ErrorCategory.TYPE_MISMATCH
        elif "too few arguments" in msg_lower or "too many arguments" in msg_lower or "argument" in msg_lower:
            category = ErrorCategory.FUNCTION_CALL
        elif "return" in msg_lower or "void function" in msg_lower:
            category = ErrorCategory.RETURN_TYPE
        elif "invalid operands" in msg_lower:
            category = ErrorCategory.INCOMPATIBLE_OPERATION
        elif "expected" in msg_lower or "syntax error" in msg_lower:
            category = ErrorCategory.SYNTAX_ERROR

        finding = DiagnosticFinding(
            id=f"TM_{lang_code.upper()}_{uuid.uuid4().hex[:8]}",
            message=msg_str,
            category=category,
            severity=severity,
            location=SourceLocation(
                file_path=file_path or f"main{default_ext}",
                line=line_num,
                column=col_num,
            ),
            origin=FindingOrigin.RULE_BASED,
            is_confirmed=True,
            rule_id=f"TM_{lang_code.upper()}_{category.name}",
            explanation=f"{lang_code.upper()} compiler diagnostic: {msg_str}",
        )

        if category == ErrorCategory.SYNTAX_ERROR and syntax_error_finding is None:
            syntax_error_finding = finding
        findings.append(finding)

    return findings, syntax_error_finding


class CLanguageAdapter(BaseLanguageAdapter):
    """Adapter for C source code using GCC/Clang/MSVC syntax-only analysis."""

    def __init__(self) -> None:
        super().__init__(
            language_id="c",
            display_name="C",
            extensions=[".c", ".h"],
            analyzer_id="c_compiler_syntax_only",
            tool_name="C Compiler (gcc/clang/cl)",
            description="Static type and syntax verification using C compiler diagnostics (-fsyntax-only).",
            install_instructions=(
                "Install GCC or Clang: "
                "Windows: run 'winget install LLVM.LLVM' or 'winget install MSYS2.MSYS2', "
                "or install Visual Studio Build Tools with C++ workload. Ensure gcc/clang/cl is on PATH."
            ),
            is_ml_supported=False,
        )

    def is_tool_available(self) -> bool:
        return find_c_compiler() is not None

    def analyze(
        self,
        source_code: str,
        file_path: Optional[str] = None,
    ) -> AnalysisResponse:
        compiler_info = find_c_compiler()
        if not compiler_info:
            return self.create_tool_unavailable_response(source_code, file_path)

        binary, kind = compiler_info
        start_time = time.perf_counter()
        lines_count = len([line for line in source_code.splitlines() if line.strip()])

        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_file = os.path.join(tmp_dir, "source.c")
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(source_code)

            if kind == "gnu":
                cmd = [binary, "-fsyntax-only", "-Wall", temp_file]
            else:
                cmd = [binary, "/Zs", "/W3", temp_file]

            returncode, stdout, stderr = safe_subprocess_run(cmd, timeout_sec=8.0, cwd=tmp_dir)

        execution_time = (time.perf_counter() - start_time) * 1000.0
        findings, syntax_err = _parse_c_cpp_diagnostics(stderr + "\n" + stdout, file_path, "c", ".c")

        category_counts: Dict[str, int] = {}
        severity_counts: Dict[str, int] = {}
        for f in findings:
            c = f.category.value
            s = f.severity.value
            category_counts[c] = category_counts.get(c, 0) + 1
            severity_counts[s] = severity_counts.get(s, 0) + 1

        summary = AnalysisSummary(
            total_findings=len(findings),
            rule_based_findings=len(findings),
            ml_predicted_findings=0,
            errors_count=severity_counts.get("error", 0),
            warnings_count=severity_counts.get("warning", 0),
            syntax_errors_count=1 if syntax_err else 0,
            category_counts=category_counts,
            severity_counts=severity_counts,
            execution_time_ms=round(execution_time, 2),
            lines_analyzed=lines_count,
        )

        return AnalysisResponse(
            status="syntax_error" if (syntax_err and len(findings) == 1) else "success",
            language=self.language_id,
            analyzer_id=self.analyzer_id,
            support_level=LanguageSupportLevel.SUPPORTED.value,
            status_message=f"C compiler analyzed {lines_count} lines ({len(findings)} findings).",
            syntax_error=syntax_err,
            findings=findings,
            summary=summary,
            server_version=self.settings.app_version,
        )


class CppLanguageAdapter(BaseLanguageAdapter):
    """Adapter for C++ source code using G++/Clang++/MSVC syntax-only analysis."""

    def __init__(self) -> None:
        super().__init__(
            language_id="cpp",
            display_name="C++",
            extensions=[".cpp", ".cc", ".cxx", ".hpp", ".hxx", ".hh"],
            analyzer_id="cpp_compiler_syntax_only",
            tool_name="C++ Compiler (g++/clang++/cl)",
            description="Static type and template diagnostics using C++ compiler (-fsyntax-only -std=c++20).",
            install_instructions=(
                "Install G++ or Clang++: "
                "Windows: run 'winget install LLVM.LLVM' or 'winget install MSYS2.MSYS2', "
                "or install Visual Studio Build Tools. Ensure g++/clang++/cl is on PATH."
            ),
            is_ml_supported=False,
        )

    def is_tool_available(self) -> bool:
        return find_cpp_compiler() is not None

    def analyze(
        self,
        source_code: str,
        file_path: Optional[str] = None,
    ) -> AnalysisResponse:
        compiler_info = find_cpp_compiler()
        if not compiler_info:
            return self.create_tool_unavailable_response(source_code, file_path)

        binary, kind = compiler_info
        start_time = time.perf_counter()
        lines_count = len([line for line in source_code.splitlines() if line.strip()])

        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_file = os.path.join(tmp_dir, "source.cpp")
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(source_code)

            if kind == "gnu":
                cmd = [binary, "-fsyntax-only", "-Wall", "-std=c++20", temp_file]
            else:
                cmd = [binary, "/Zs", "/std:c++20", "/W3", temp_file]

            returncode, stdout, stderr = safe_subprocess_run(cmd, timeout_sec=8.0, cwd=tmp_dir)

        execution_time = (time.perf_counter() - start_time) * 1000.0
        findings, syntax_err = _parse_c_cpp_diagnostics(stderr + "\n" + stdout, file_path, "cpp", ".cpp")

        category_counts: Dict[str, int] = {}
        severity_counts: Dict[str, int] = {}
        for f in findings:
            c = f.category.value
            s = f.severity.value
            category_counts[c] = category_counts.get(c, 0) + 1
            severity_counts[s] = severity_counts.get(s, 0) + 1

        summary = AnalysisSummary(
            total_findings=len(findings),
            rule_based_findings=len(findings),
            ml_predicted_findings=0,
            errors_count=severity_counts.get("error", 0),
            warnings_count=severity_counts.get("warning", 0),
            syntax_errors_count=1 if syntax_err else 0,
            category_counts=category_counts,
            severity_counts=severity_counts,
            execution_time_ms=round(execution_time, 2),
            lines_analyzed=lines_count,
        )

        return AnalysisResponse(
            status="syntax_error" if (syntax_err and len(findings) == 1) else "success",
            language=self.language_id,
            analyzer_id=self.analyzer_id,
            support_level=LanguageSupportLevel.SUPPORTED.value,
            status_message=f"C++ compiler analyzed {lines_count} lines ({len(findings)} findings).",
            syntax_error=syntax_err,
            findings=findings,
            summary=summary,
            server_version=self.settings.app_version,
        )
