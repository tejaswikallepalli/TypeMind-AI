"""TypeScript language adapter using the TypeScript compiler (tsc)."""

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

logger = logging.getLogger("typemind.languages.typescript")

# Pattern: filepath(line,col): error/warning TSxxxx: message
TSC_DIAGNOSTIC_REGEX = re.compile(
    r"^.*?\((?P<line>\d+),(?P<col>\d+)\):\s*(?P<severity>error|warning)\s+(?P<code>TS\d+):\s*(?P<msg>.*)$"
)
TYPE_ASSIGN_REGEX = re.compile(
    r"Type '(?P<found>[^']+)' is not assignable to type '(?P<expected>[^']+)'"
)


def find_tsc_runner() -> Optional[List[str]]:
    """Locate tsc binary or node running frontend/node_modules/typescript/lib/tsc.js."""
    # 1. System tsc
    tsc_cli = shutil.which("tsc")
    if tsc_cli:
        return [tsc_cli]

    # 2. Node runner with local package
    node_cli = shutil.which("node")
    if node_cli:
        cwd = os.getcwd()
        candidates = [
            os.path.join(cwd, "frontend", "node_modules", "typescript", "lib", "tsc.js"),
            os.path.join(cwd, "node_modules", "typescript", "lib", "tsc.js"),
            os.path.join(os.path.dirname(cwd), "frontend", "node_modules", "typescript", "lib", "tsc.js"),
        ]
        for cand in candidates:
            if os.path.exists(cand):
                return [node_cli, cand]

    return None


class TypeScriptLanguageAdapter(BaseLanguageAdapter):
    """Adapter for TypeScript analysis using TypeScript compiler diagnostics without program execution."""

    def __init__(self) -> None:
        super().__init__(
            language_id="typescript",
            display_name="TypeScript",
            extensions=[".ts", ".tsx", ".mts", ".cts"],
            analyzer_id="typescript_tsc_compiler",
            tool_name="TypeScript Compiler (tsc)",
            description="Static type checking using TypeScript compiler diagnostics (tsc --noEmit).",
            install_instructions="Install Node.js and TypeScript: npm install -g typescript (or via project dependencies).",
            is_ml_supported=False,
        )

    def is_tool_available(self) -> bool:
        """Returns True if tsc or node + tsc.js is executable."""
        return find_tsc_runner() is not None

    def analyze(
        self,
        source_code: str,
        file_path: Optional[str] = None,
    ) -> AnalysisResponse:
        """Run TypeScript compiler in --noEmit mode on a secure temporary source file."""
        runner = find_tsc_runner()
        if not runner:
            return self.create_tool_unavailable_response(source_code, file_path)

        start_time = time.perf_counter()
        lines_count = len([line for line in source_code.splitlines() if line.strip()])

        ext = ".tsx" if (file_path and file_path.endswith(".tsx")) else ".ts"

        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_file = os.path.join(tmp_dir, f"source{ext}")
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(source_code)

            cmd = [
                *runner,
                "--noEmit",
                "--target", "es2022",
                "--module", "commonjs",
                "--skipLibCheck",
                temp_file,
            ]

            returncode, stdout, stderr = safe_subprocess_run(cmd, timeout_sec=10.0, cwd=tmp_dir)

        execution_time = (time.perf_counter() - start_time) * 1000.0

        output_text = stdout + "\n" + stderr
        findings: List[DiagnosticFinding] = []
        syntax_error_finding: Optional[DiagnosticFinding] = None

        for line in output_text.splitlines():
            line_str = line.strip()
            if not line_str:
                continue

            match = TSC_DIAGNOSTIC_REGEX.match(line_str)
            if not match:
                continue

            line_num = int(match.group("line"))
            col_num = int(match.group("col"))
            sev_str = match.group("severity").lower()
            code_str = match.group("code")
            msg_str = match.group("msg")

            severity = Severity.ERROR if sev_str == "error" else Severity.WARNING

            # Category classification
            category = ErrorCategory.TYPE_MISMATCH
            if "argument" in msg_str.lower() or code_str in ("TS2554", "TS2555", "TS2556"):
                category = ErrorCategory.FUNCTION_CALL
            elif "return" in msg_str.lower() or code_str in ("TS2366", "TS2355"):
                category = ErrorCategory.RETURN_TYPE
            elif "operator" in msg_str.lower() or "incompatible" in msg_str.lower():
                category = ErrorCategory.INCOMPATIBLE_OPERATION
            elif code_str in ("TS1005", "TS1109", "TS1128", "TS1161"):
                category = ErrorCategory.SYNTAX_ERROR

            # Type extraction if pattern matches
            expected_type: Optional[TypeInfo] = None
            observed_type: Optional[TypeInfo] = None
            type_match = TYPE_ASSIGN_REGEX.search(msg_str)
            if type_match:
                observed_type = TypeInfo(raw_type=type_match.group("found"), is_inferred=True)
                expected_type = TypeInfo(raw_type=type_match.group("expected"), is_inferred=False)

            finding = DiagnosticFinding(
                id=f"TM_TS_{code_str}_{uuid.uuid4().hex[:8]}",
                message=f"[{code_str}] {msg_str}",
                category=category,
                severity=severity,
                location=SourceLocation(
                    file_path=file_path or f"input{ext}",
                    line=line_num,
                    column=col_num,
                ),
                origin=FindingOrigin.RULE_BASED,
                is_confirmed=True,
                rule_id=f"TM_TS_{code_str}",
                expected_type=expected_type,
                observed_type=observed_type,
                explanation=f"TypeScript compiler diagnostic {code_str}: {msg_str}",
            )

            if category == ErrorCategory.SYNTAX_ERROR and syntax_error_finding is None:
                syntax_error_finding = finding
            findings.append(finding)

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
            syntax_errors_count=1 if syntax_error_finding else 0,
            category_counts=category_counts,
            severity_counts=severity_counts,
            execution_time_ms=round(execution_time, 2),
            lines_analyzed=lines_count,
        )

        status_str = "syntax_error" if (syntax_error_finding and len(findings) == 1) else "success"

        return AnalysisResponse(
            status=status_str,
            language=self.language_id,
            analyzer_id=self.analyzer_id,
            support_level=LanguageSupportLevel.SUPPORTED.value,
            status_message=f"TypeScript compiler analyzed {lines_count} lines ({len(findings)} findings).",
            syntax_error=syntax_error_finding,
            findings=findings,
            summary=summary,
            server_version=self.settings.app_version,
        )
