"""Go language adapter using go vet / go compiler checks."""

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

logger = logging.getLogger("typemind.languages.go")

GO_DIAGNOSTIC_REGEX = re.compile(
    r"^.*?:(?P<line>\d+):(?P<col>\d+):\s*(?P<msg>.*)$"
)


class GoLanguageAdapter(BaseLanguageAdapter):
    """Adapter for Go source code using go vet / go compiler diagnostics."""

    def __init__(self) -> None:
        super().__init__(
            language_id="go",
            display_name="Go",
            extensions=[".go"],
            analyzer_id="go_toolchain_vet",
            tool_name="Go Toolchain (go vet/build)",
            description="Static type and semantic checking using the Go compiler and vet tooling.",
            install_instructions="Install Go toolchain: https://go.dev/dl/ or run 'winget install GoLang.Go'.",
            is_ml_supported=False,
        )

    def is_tool_available(self) -> bool:
        return shutil.which("go") is not None

    def analyze(
        self,
        source_code: str,
        file_path: Optional[str] = None,
    ) -> AnalysisResponse:
        if not self.is_tool_available():
            return self.create_tool_unavailable_response(source_code, file_path)
        go_cli = shutil.which("go") or "go"

        start_time = time.perf_counter()
        lines_count = len([line for line in source_code.splitlines() if line.strip()])

        findings: List[DiagnosticFinding] = []
        syntax_error_finding: Optional[DiagnosticFinding] = None

        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_file = os.path.join(tmp_dir, "main.go")
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(source_code)

            # Initialize a temporary go.mod to allow go vet / build
            safe_subprocess_run([go_cli, "mod", "init", "tempmodule"], timeout_sec=5.0, cwd=tmp_dir)

            cmd = [go_cli, "vet", "./..."]
            returncode, stdout, stderr = safe_subprocess_run(cmd, timeout_sec=8.0, cwd=tmp_dir)

            if returncode != 0 and not stderr:
                # Try compile check
                cmd_build = [go_cli, "build", "-o", os.devnull, "."]
                returncode, stdout, stderr = safe_subprocess_run(cmd_build, timeout_sec=8.0, cwd=tmp_dir)

        execution_time = (time.perf_counter() - start_time) * 1000.0
        output_text = stderr + "\n" + stdout

        for line in output_text.splitlines():
            line_str = line.strip()
            if not line_str or line_str.startswith("#"):
                continue

            match = GO_DIAGNOSTIC_REGEX.match(line_str)
            if not match:
                continue

            line_num = int(match.group("line"))
            col_num = int(match.group("col"))
            msg_str = match.group("msg").strip()

            category = ErrorCategory.TYPE_MISMATCH
            msg_lower = msg_str.lower()
            if "cannot use" in msg_lower and "as" in msg_lower or "mismatched types" in msg_lower:
                category = ErrorCategory.TYPE_MISMATCH
            elif "too many arguments" in msg_lower or "not enough arguments" in msg_lower:
                category = ErrorCategory.FUNCTION_CALL
            elif "missing return" in msg_lower or "too many return values" in msg_lower:
                category = ErrorCategory.RETURN_TYPE
            elif "invalid operation" in msg_lower:
                category = ErrorCategory.INCOMPATIBLE_OPERATION
            elif "syntax error" in msg_lower or "expected" in msg_lower:
                category = ErrorCategory.SYNTAX_ERROR

            finding = DiagnosticFinding(
                id=f"TM_GO_{uuid.uuid4().hex[:8]}",
                message=msg_str,
                category=category,
                severity=Severity.ERROR,
                location=SourceLocation(
                    file_path=file_path or "main.go",
                    line=line_num,
                    column=col_num,
                ),
                origin=FindingOrigin.RULE_BASED,
                is_confirmed=True,
                rule_id=f"TM_GO_{category.name}",
                explanation=f"Go static analyzer diagnostic: {msg_str}",
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
            status_message=f"Go toolchain analyzed {lines_count} lines ({len(findings)} findings).",
            syntax_error=syntax_error_finding,
            findings=findings,
            summary=summary,
            server_version=self.settings.app_version,
        )
