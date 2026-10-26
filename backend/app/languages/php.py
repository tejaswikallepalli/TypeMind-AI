"""PHP language adapter using PHP linting (php -l)."""

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

logger = logging.getLogger("typemind.languages.php")

# Pattern: Parse error: syntax error, unexpected '...' in file.php on line 12
PHP_LINT_REGEX = re.compile(
    r"(?P<sev>Parse error|Fatal error):\s*(?P<msg>.*?)\s+in\s+.*?\s+on line\s+(?P<line>\d+)",
    re.IGNORECASE,
)


class PhpLanguageAdapter(BaseLanguageAdapter):
    """Adapter for PHP source code using php -l syntax and fatal error linting."""

    def __init__(self) -> None:
        super().__init__(
            language_id="php",
            display_name="PHP",
            extensions=[".php", ".phtml"],
            analyzer_id="php_cli_linter",
            tool_name="PHP CLI (php -l)",
            description="PHP syntax checking and fatal error linting (php -l).",
            install_instructions="Install PHP CLI: https://windows.php.net/download/ or run 'winget install PHP.PHP'.",
            is_ml_supported=False,
        )

    def is_tool_available(self) -> bool:
        return shutil.which("php") is not None

    def get_support_level(self) -> LanguageSupportLevel:
        if not self.is_tool_available():
            return LanguageSupportLevel.TOOL_UNAVAILABLE
        return LanguageSupportLevel.PARTIAL

    def analyze(
        self,
        source_code: str,
        file_path: Optional[str] = None,
    ) -> AnalysisResponse:
        php_cli = shutil.which("php")
        if not php_cli:
            return self.create_tool_unavailable_response(source_code, file_path)

        start_time = time.perf_counter()
        lines_count = len([line for line in source_code.splitlines() if line.strip()])

        findings: List[DiagnosticFinding] = []
        syntax_error_finding: Optional[DiagnosticFinding] = None

        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_file = os.path.join(tmp_dir, "script.php")
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(source_code)

            cmd = [php_cli, "-l", temp_file]
            returncode, stdout, stderr = safe_subprocess_run(cmd, timeout_sec=5.0, cwd=tmp_dir)

        execution_time = (time.perf_counter() - start_time) * 1000.0
        output_text = stdout + "\n" + stderr

        for line in output_text.splitlines():
            match = PHP_LINT_REGEX.search(line)
            if not match:
                continue

            msg_str = match.group("msg").strip()
            line_num = int(match.group("line"))

            finding = DiagnosticFinding(
                id=f"TM_PHP_{uuid.uuid4().hex[:8]}",
                message=f"PHP Syntax Error: {msg_str}",
                category=ErrorCategory.SYNTAX_ERROR,
                severity=Severity.ERROR,
                location=SourceLocation(
                    file_path=file_path or "script.php",
                    line=line_num,
                    column=1,
                ),
                origin=FindingOrigin.RULE_BASED,
                is_confirmed=True,
                rule_id="TM_PHP_SYNTAX_ERROR",
                explanation=f"PHP parser fatal error at line {line_num}: {msg_str}",
            )
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
            syntax_errors_count=len(findings),
            category_counts=category_counts,
            severity_counts=severity_counts,
            execution_time_ms=round(execution_time, 2),
            lines_analyzed=lines_count,
        )

        return AnalysisResponse(
            status="syntax_error" if syntax_error_finding else "success",
            language=self.language_id,
            analyzer_id=self.analyzer_id,
            support_level=LanguageSupportLevel.PARTIAL.value,
            status_message=f"PHP CLI linted {lines_count} lines ({len(findings)} findings).",
            syntax_error=syntax_error_finding,
            findings=findings,
            summary=summary,
            server_version=self.settings.app_version,
        )
