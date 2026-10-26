"""Java language adapter using the Java Compiler (javac)."""

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
from app.schemas.common import ErrorCategory, FindingOrigin, Severity, SourceLocation, TypeInfo
from app.schemas.diagnostics import DiagnosticFinding
from app.schemas.languages import LanguageSupportLevel

logger = logging.getLogger("typemind.languages.java")

# Pattern: filename.java:12: error/warning: message
JAVAC_DIAGNOSTIC_REGEX = re.compile(
    r"^.*?:(?P<line>\d+):\s*(?P<severity>error|warning):\s*(?P<msg>.*)$"
)
JAVA_INCOMPATIBLE_TYPE_REGEX = re.compile(
    r"incompatible types:\s*(?P<found>[\w\.<>\[\]]+)\s*cannot be converted to\s*(?P<expected>[\w\.<>\[\]]+)"
)


class JavaLanguageAdapter(BaseLanguageAdapter):
    """Adapter for Java source code utilizing javac diagnostics without program execution."""

    def __init__(self) -> None:
        super().__init__(
            language_id="java",
            display_name="Java",
            extensions=[".java"],
            analyzer_id="java_javac_compiler",
            tool_name="Java Compiler (javac)",
            description="Static semantic and type analysis using Java compiler diagnostics (-proc:none -Xlint).",
            install_instructions=(
                "Install OpenJDK / Eclipse Temurin JDK 17+: "
                "Download from https://adoptium.net/ or run 'winget install EclipseAdoptium.Temurin.21.JDK'. "
                "Ensure 'javac' is added to system PATH."
            ),
            is_ml_supported=False,
        )

    def is_tool_available(self) -> bool:
        """Returns True if javac is found in system PATH."""
        return shutil.which("javac") is not None

    def analyze(
        self,
        source_code: str,
        file_path: Optional[str] = None,
    ) -> AnalysisResponse:
        """Execute javac static check in safe temporary sandbox."""
        if not self.is_tool_available():
            return self.create_tool_unavailable_response(source_code, file_path)

        start_time = time.perf_counter()
        lines_count = len([line for line in source_code.splitlines() if line.strip()])

        # Extract class name if declared, or default to Main
        class_match = re.search(r"public\s+class\s+([A-Za-z_0-9]+)", source_code)
        class_name = class_match.group(1) if class_match else "Main"

        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_file = os.path.join(tmp_dir, f"{class_name}.java")
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(source_code)

            cmd = [
                "javac",
                "-proc:none",  # disable annotation processing for safety
                "-Xlint",
                "-d", tmp_dir,
                temp_file,
            ]

            returncode, stdout, stderr = safe_subprocess_run(cmd, timeout_sec=10.0, cwd=tmp_dir)

        execution_time = (time.perf_counter() - start_time) * 1000.0

        output_text = stderr + "\n" + stdout
        findings: List[DiagnosticFinding] = []
        syntax_error_finding: Optional[DiagnosticFinding] = None

        for line in output_text.splitlines():
            line_str = line.strip()
            if not line_str:
                continue

            match = JAVAC_DIAGNOSTIC_REGEX.match(line_str)
            if not match:
                continue

            line_num = int(match.group("line"))
            sev_str = match.group("severity").lower()
            msg_str = match.group("msg").strip()

            severity = Severity.ERROR if sev_str == "error" else Severity.WARNING

            # Category classification
            category = ErrorCategory.TYPE_MISMATCH
            if "cannot be converted" in msg_str or "incompatible types" in msg_str:
                category = ErrorCategory.TYPE_MISMATCH
            elif "cannot be applied to given types" in msg_str or "arguments" in msg_str:
                category = ErrorCategory.FUNCTION_CALL
            elif "missing return statement" in msg_str or "incompatible types: unexpected return value" in msg_str:
                category = ErrorCategory.RETURN_TYPE
            elif "bad operand types" in msg_str:
                category = ErrorCategory.INCOMPATIBLE_OPERATION
            elif "reached end of file while parsing" in msg_str or "expected" in msg_str:
                category = ErrorCategory.SYNTAX_ERROR

            expected_type: Optional[TypeInfo] = None
            observed_type: Optional[TypeInfo] = None
            type_match = JAVA_INCOMPATIBLE_TYPE_REGEX.search(msg_str)
            if type_match:
                observed_type = TypeInfo(raw_type=type_match.group("found"), is_inferred=True)
                expected_type = TypeInfo(raw_type=type_match.group("expected"), is_inferred=False)

            rule_code = "TM_JAVA_TYPE_MISMATCH" if category == ErrorCategory.TYPE_MISMATCH else f"TM_JAVA_{category.name}"

            finding = DiagnosticFinding(
                id=f"TM_JAVA_{uuid.uuid4().hex[:8]}",
                message=msg_str,
                category=category,
                severity=severity,
                location=SourceLocation(
                    file_path=file_path or f"{class_name}.java",
                    line=line_num,
                    column=1,
                ),
                origin=FindingOrigin.RULE_BASED,
                is_confirmed=True,
                rule_id=rule_code,
                expected_type=expected_type,
                observed_type=observed_type,
                explanation=f"Java compiler (javac) diagnostic: {msg_str}",
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
            status_message=f"Java compiler analyzed {lines_count} lines ({len(findings)} findings).",
            syntax_error=syntax_error_finding,
            findings=findings,
            summary=summary,
            server_version=self.settings.app_version,
        )
