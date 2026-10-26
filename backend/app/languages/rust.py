"""Rust language adapter using rustc JSON diagnostics."""

from __future__ import annotations
import json
import logging
import os
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

logger = logging.getLogger("typemind.languages.rust")


class RustLanguageAdapter(BaseLanguageAdapter):
    """Adapter for Rust source code using rustc --emit=metadata JSON diagnostics without program execution."""

    def __init__(self) -> None:
        super().__init__(
            language_id="rust",
            display_name="Rust",
            extensions=[".rs"],
            analyzer_id="rust_compiler_rustc",
            tool_name="Rust Compiler (rustc)",
            description="Static type and borrow checking using rustc compiler diagnostics (--emit=metadata).",
            install_instructions="Install Rust toolchain: https://rustup.rs/ or run 'winget install Rustlang.Rustup'.",
            is_ml_supported=False,
        )

    def is_tool_available(self) -> bool:
        return shutil.which("rustc") is not None

    def analyze(
        self,
        source_code: str,
        file_path: Optional[str] = None,
    ) -> AnalysisResponse:
        if not self.is_tool_available():
            return self.create_tool_unavailable_response(source_code, file_path)
        rustc_cli = shutil.which("rustc") or "rustc"

        start_time = time.perf_counter()
        lines_count = len([line for line in source_code.splitlines() if line.strip()])

        findings: List[DiagnosticFinding] = []
        syntax_error_finding: Optional[DiagnosticFinding] = None

        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_file = os.path.join(tmp_dir, "main.rs")
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(source_code)

            cmd = [
                rustc_cli,
                "--error-format=json",
                "--emit=metadata",
                "-o", os.path.join(tmp_dir, "lib.rmeta"),
                temp_file,
            ]
            returncode, stdout, stderr = safe_subprocess_run(cmd, timeout_sec=10.0, cwd=tmp_dir)

        execution_time = (time.perf_counter() - start_time) * 1000.0

        for line in stderr.splitlines():
            line_str = line.strip()
            if not line_str.startswith("{"):
                continue

            try:
                diag = json.loads(line_str)
            except Exception:
                continue

            msg = diag.get("message", "")
            level = diag.get("level", "error")
            code_obj = diag.get("code")
            code_str = code_obj.get("code") if isinstance(code_obj, dict) else "E0000"
            spans = diag.get("spans", [])

            line_num = 1
            col_num = 1
            if spans:
                primary = next((s for s in spans if s.get("is_primary")), spans[0])
                line_num = primary.get("line_start", 1)
                col_num = primary.get("column_start", 1)

            severity = Severity.ERROR if level == "error" else Severity.WARNING

            category = ErrorCategory.TYPE_MISMATCH
            msg_lower = msg.lower()
            if "mismatched types" in msg_lower or code_str == "E0308":
                category = ErrorCategory.TYPE_MISMATCH
            elif "arguments" in msg_lower or code_str in ("E0061", "E0060"):
                category = ErrorCategory.FUNCTION_CALL
            elif "return" in msg_lower or code_str == "E0269":
                category = ErrorCategory.RETURN_TYPE
            elif "cannot be applied" in msg_lower or "operator" in msg_lower:
                category = ErrorCategory.INCOMPATIBLE_OPERATION
            elif "syntax error" in msg_lower or "expected" in msg_lower:
                category = ErrorCategory.SYNTAX_ERROR

            finding = DiagnosticFinding(
                id=f"TM_RUST_{code_str}_{uuid.uuid4().hex[:8]}",
                message=f"[{code_str}] {msg}",
                category=category,
                severity=severity,
                location=SourceLocation(
                    file_path=file_path or "main.rs",
                    line=line_num,
                    column=col_num,
                ),
                origin=FindingOrigin.RULE_BASED,
                is_confirmed=True,
                rule_id=f"TM_RUST_{code_str}",
                explanation=f"Rust compiler (rustc) diagnostic {code_str}: {msg}",
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
            status_message=f"Rust compiler analyzed {lines_count} lines ({len(findings)} findings).",
            syntax_error=syntax_error_finding,
            findings=findings,
            summary=summary,
            server_version=self.settings.app_version,
        )
