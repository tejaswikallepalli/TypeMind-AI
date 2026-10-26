"""C# language adapter using Roslyn (csc) or dotnet build."""

from __future__ import annotations
import logging
import os
import re
import shutil
import tempfile
import time
import uuid
from typing import Dict, List, Optional

from app.languages.base import BaseLanguageAdapter, safe_subprocess_run
from app.schemas.analysis import AnalysisResponse, AnalysisSummary
from app.schemas.common import ErrorCategory, FindingOrigin, Severity, SourceLocation
from app.schemas.diagnostics import DiagnosticFinding
from app.schemas.languages import LanguageSupportLevel

logger = logging.getLogger("typemind.languages.csharp")

# Pattern: filename.cs(12,5): error CS0029: Cannot implicitly convert type 'string' to 'int'
CSHARP_REGEX = re.compile(
    r"^.*?\((?P<line>\d+),(?P<col>\d+)\):\s*(?P<severity>error|warning)\s+(?P<code>CS\d+):\s*(?P<msg>.*)$"
)


class CSharpLanguageAdapter(BaseLanguageAdapter):
    """Adapter for C# source code using Roslyn compiler diagnostics without program execution."""

    def __init__(self) -> None:
        super().__init__(
            language_id="csharp",
            display_name="C#",
            extensions=[".cs"],
            analyzer_id="csharp_roslyn_compiler",
            tool_name="C# Roslyn Compiler (csc/dotnet)",
            description="Static type and semantic checking via Roslyn compiler diagnostics (csc /t:module).",
            install_instructions="Install .NET SDK (8.0+): https://dotnet.microsoft.com/download or run 'winget install Microsoft.DotNet.SDK.8'.",
            is_ml_supported=False,
        )

    def is_tool_available(self) -> bool:
        return shutil.which("csc") is not None or shutil.which("dotnet") is not None

    def analyze(
        self,
        source_code: str,
        file_path: Optional[str] = None,
    ) -> AnalysisResponse:
        if not self.is_tool_available():
            return self.create_tool_unavailable_response(source_code, file_path)
        csc_cli = shutil.which("csc")

        start_time = time.perf_counter()
        lines_count = len([line for line in source_code.splitlines() if line.strip()])

        findings: List[DiagnosticFinding] = []
        syntax_error_finding: Optional[DiagnosticFinding] = None

        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_file = os.path.join(tmp_dir, "Program.cs")
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(source_code)

            if csc_cli:
                cmd = [csc_cli, "/t:module", "/nologo", temp_file]
            else:
                cmd = ["dotnet", "build", temp_file, "--nologo"]

            returncode, stdout, stderr = safe_subprocess_run(cmd, timeout_sec=10.0, cwd=tmp_dir)

        execution_time = (time.perf_counter() - start_time) * 1000.0
        output_text = stdout + "\n" + stderr

        for line in output_text.splitlines():
            line_str = line.strip()
            if not line_str:
                continue

            match = CSHARP_REGEX.match(line_str)
            if not match:
                continue

            line_num = int(match.group("line"))
            col_num = int(match.group("col"))
            sev_str = match.group("severity").lower()
            code_str = match.group("code")
            msg_str = match.group("msg").strip()

            severity = Severity.ERROR if sev_str == "error" else Severity.WARNING

            category = ErrorCategory.TYPE_MISMATCH
            msg_lower = msg_str.lower()
            if "convert type" in msg_lower or "cannot implicitly convert" in msg_lower:
                category = ErrorCategory.TYPE_MISMATCH
            elif "no overload for method" in msg_lower or "takes" in msg_lower and "arguments" in msg_lower:
                category = ErrorCategory.FUNCTION_CALL
            elif "not all code paths return a value" in msg_lower or "cannot return a value" in msg_lower:
                category = ErrorCategory.RETURN_TYPE
            elif "operator" in msg_lower and "cannot be applied" in msg_lower:
                category = ErrorCategory.INCOMPATIBLE_OPERATION
            elif code_str in ("CS1002", "CS1513", "CS1519"):
                category = ErrorCategory.SYNTAX_ERROR

            finding = DiagnosticFinding(
                id=f"TM_CS_{code_str}_{uuid.uuid4().hex[:8]}",
                message=f"[{code_str}] {msg_str}",
                category=category,
                severity=severity,
                location=SourceLocation(
                    file_path=file_path or "Program.cs",
                    line=line_num,
                    column=col_num,
                ),
                origin=FindingOrigin.RULE_BASED,
                is_confirmed=True,
                rule_id=f"TM_CS_{code_str}",
                explanation=f"C# Roslyn diagnostic {code_str}: {msg_str}",
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

        return AnalysisResponse(
            status="syntax_error" if (syntax_error_finding and len(findings) == 1) else "success",
            language=self.language_id,
            analyzer_id=self.analyzer_id,
            support_level=LanguageSupportLevel.SUPPORTED.value,
            status_message=f"C# Roslyn compiler analyzed {lines_count} lines ({len(findings)} findings).",
            syntax_error=syntax_error_finding,
            findings=findings,
            summary=summary,
            server_version=self.settings.app_version,
        )
