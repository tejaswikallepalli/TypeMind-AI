"""JavaScript language adapter using TypeScript/Node toolchain for type and syntax analysis."""

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
from app.languages.typescript import TSC_DIAGNOSTIC_REGEX, TYPE_ASSIGN_REGEX, find_tsc_runner
from app.schemas.analysis import AnalysisResponse, AnalysisSummary
from app.schemas.common import ErrorCategory, FindingOrigin, Severity, SourceLocation, TypeInfo
from app.schemas.diagnostics import DiagnosticFinding
from app.schemas.languages import LanguageSupportLevel

logger = logging.getLogger("typemind.languages.javascript")


class JavaScriptLanguageAdapter(BaseLanguageAdapter):
    """Adapter for JavaScript source code analyzing syntax errors, JSDoc types, and inferred type mismatches."""

    def __init__(self) -> None:
        super().__init__(
            language_id="javascript",
            display_name="JavaScript",
            extensions=[".js", ".jsx", ".mjs", ".cjs"],
            analyzer_id="javascript_tsc_analyzer",
            tool_name="JavaScript Type & Syntax Engine (tsc/Node)",
            description="JavaScript static analysis with type checking via JSDoc/inference and syntax verification.",
            install_instructions="Install Node.js: https://nodejs.org/ (Node and npm).",
            is_ml_supported=False,
        )

    def is_tool_available(self) -> bool:
        """Returns True if tsc runner or node is available."""
        return find_tsc_runner() is not None or shutil.which("node") is not None

    def analyze(
        self,
        source_code: str,
        file_path: Optional[str] = None,
    ) -> AnalysisResponse:
        """Analyze JavaScript using tsc --allowJs --checkJs --noEmit or fallback to node --check."""
        runner = find_tsc_runner()
        node_cli = shutil.which("node")

        if not runner and not node_cli:
            return self.create_tool_unavailable_response(source_code, file_path)

        start_time = time.perf_counter()
        lines_count = len([line for line in source_code.splitlines() if line.strip()])
        ext = ".jsx" if (file_path and file_path.endswith(".jsx")) else ".js"

        findings: List[DiagnosticFinding] = []
        syntax_error_finding: Optional[DiagnosticFinding] = None

        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_file = os.path.join(tmp_dir, f"source{ext}")
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(source_code)

            if runner:
                cmd = [
                    *runner,
                    "--allowJs",
                    "--checkJs",
                    "--noEmit",
                    "--target", "es2022",
                    "--module", "commonjs",
                    "--skipLibCheck",
                    temp_file,
                ]
                returncode, stdout, stderr = safe_subprocess_run(cmd, timeout_sec=10.0, cwd=tmp_dir)
                output_text = stdout + "\n" + stderr

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
                    category = ErrorCategory.TYPE_MISMATCH
                    if "argument" in msg_str.lower() or code_str in ("TS2554", "TS2555"):
                        category = ErrorCategory.FUNCTION_CALL
                    elif "return" in msg_str.lower() or code_str in ("TS2366", "TS2355"):
                        category = ErrorCategory.RETURN_TYPE
                    elif code_str in ("TS1005", "TS1109", "TS1128"):
                        category = ErrorCategory.SYNTAX_ERROR

                    expected_type: Optional[TypeInfo] = None
                    observed_type: Optional[TypeInfo] = None
                    type_match = TYPE_ASSIGN_REGEX.search(msg_str)
                    if type_match:
                        observed_type = TypeInfo(raw_type=type_match.group("found"), is_inferred=True)
                        expected_type = TypeInfo(raw_type=type_match.group("expected"), is_inferred=False)

                    finding = DiagnosticFinding(
                        id=f"TM_JS_{code_str}_{uuid.uuid4().hex[:8]}",
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
                        rule_id=f"TM_JS_{code_str}",
                        expected_type=expected_type,
                        observed_type=observed_type,
                        explanation=f"JavaScript static analysis diagnostic {code_str}: {msg_str}",
                    )
                    if category == ErrorCategory.SYNTAX_ERROR and syntax_error_finding is None:
                        syntax_error_finding = finding
                    findings.append(finding)
            elif node_cli:
                # Fallback to node syntax check
                cmd = [node_cli, "--check", temp_file]
                returncode, stdout, stderr = safe_subprocess_run(cmd, timeout_sec=5.0, cwd=tmp_dir)
                if returncode != 0:
                    syntax_finding = DiagnosticFinding(
                        id=f"TM_JS_SYNTAX_{uuid.uuid4().hex[:8]}",
                        message=f"JavaScript syntax error: {stderr.strip()[:160]}",
                        category=ErrorCategory.SYNTAX_ERROR,
                        severity=Severity.ERROR,
                        location=SourceLocation(file_path=file_path or f"input{ext}", line=1, column=1),
                        origin=FindingOrigin.RULE_BASED,
                        is_confirmed=True,
                        rule_id="TM_JS_SYNTAX_ERROR",
                        explanation=stderr.strip(),
                    )
                    syntax_error_finding = syntax_finding
                    findings.append(syntax_finding)

        execution_time = (time.perf_counter() - start_time) * 1000.0

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
            status_message=f"JavaScript static analysis analyzed {lines_count} lines ({len(findings)} findings).",
            syntax_error=syntax_error_finding,
            findings=findings,
            summary=summary,
            server_version=self.settings.app_version,
        )
