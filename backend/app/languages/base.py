"""Base abstract class and execution infrastructure for multi-language semantic analyzers."""

from __future__ import annotations
from abc import ABC, abstractmethod
import logging
import os
import shutil
import subprocess
import time
import uuid
from typing import List, Optional, Tuple

from app.core.config import get_settings
from app.schemas.analysis import AnalysisResponse, AnalysisSummary
from app.schemas.common import ErrorCategory, FindingOrigin, Severity, SourceLocation
from app.schemas.diagnostics import DiagnosticFinding
from app.schemas.languages import LanguageInfo, LanguageSupportLevel

logger = logging.getLogger("typemind.languages.base")


def safe_subprocess_run(
    cmd: List[str],
    timeout_sec: float = 8.0,
    cwd: Optional[str] = None,
    input_text: Optional[str] = None,
) -> Tuple[int, str, str]:
    """Execute a compiler or static analyzer command safely with strict isolation and timeout.

    Never executes submitted program binaries or package lifecycle scripts.
    """
    try:
        proc = subprocess.run(
            cmd,
            input=input_text,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout_sec,
            shell=False,  # strictly prevent shell injection
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        logger.warning("Subprocess timed out after %.1fs: %s", timeout_sec, " ".join(cmd[:3]))
        return -1, "", f"Analysis execution timed out after {timeout_sec} seconds."
    except FileNotFoundError:
        logger.warning("Executable not found: %s", cmd[0] if cmd else "None")
        return -2, "", f"Required executable not found: {cmd[0] if cmd else 'unknown'}"
    except Exception as exc:
        logger.error("Error executing analyzer command: %s", exc)
        return -3, "", f"Analyzer execution failed: {str(exc)}"


class BaseLanguageAdapter(ABC):
    """Abstract base contract for language-specific type and semantic analyzers."""

    def __init__(
        self,
        language_id: str,
        display_name: str,
        extensions: List[str],
        analyzer_id: str,
        tool_name: str,
        description: str,
        install_instructions: str,
        is_ml_supported: bool = False,
    ) -> None:
        self.language_id = language_id
        self.display_name = display_name
        self.extensions = [ext.lower() for ext in extensions]
        self.analyzer_id = analyzer_id
        self.tool_name = tool_name
        self.description = description
        self.install_instructions = install_instructions
        self.is_ml_supported = is_ml_supported
        self.settings = get_settings()

    @abstractmethod
    def is_tool_available(self) -> bool:
        """Check if required external toolchain or runtime is installed on the host."""
        ...

    def get_support_level(self) -> LanguageSupportLevel:
        """Determine current operational support level."""
        if not self.is_tool_available():
            return LanguageSupportLevel.TOOL_UNAVAILABLE
        return LanguageSupportLevel.SUPPORTED

    def get_info(self) -> LanguageInfo:
        """Export standardized language capabilities metadata."""
        return LanguageInfo(
            id=self.language_id,
            name=self.display_name,
            extensions=self.extensions,
            support_level=self.get_support_level(),
            tool_name=self.tool_name,
            tool_available=self.is_tool_available(),
            ml_supported=self.is_ml_supported,
            description=self.description,
            setup_instructions=self.install_instructions if not self.is_tool_available() else None,
        )

    def create_tool_unavailable_response(
        self,
        source_code: str,
        file_path: Optional[str] = None,
    ) -> AnalysisResponse:
        """Generate structured response when required language toolchain is missing."""
        lines_count = len([line for line in source_code.splitlines() if line.strip()])
        msg = f"{self.display_name} analyzer tool '{self.tool_name}' is not available on this system."

        finding = DiagnosticFinding(
            id=f"TM_TOOL_MISSING_{self.language_id.upper()}_{uuid.uuid4().hex[:8]}",
            message=msg,
            category=ErrorCategory.SYNTAX_ERROR,
            severity=Severity.WARNING,
            location=SourceLocation(file_path=file_path, line=1, column=1),
            origin=FindingOrigin.RULE_BASED,
            is_confirmed=True,
            rule_id=f"TM_ENV_{self.language_id.upper()}_UNAVAILABLE",
            explanation=(
                f"Cannot analyze {self.display_name} source code because the required compiler/analyzer "
                f"('{self.tool_name}') is not installed or not in the system PATH.\n\n"
                f"Setup instructions:\n{self.install_instructions}"
            ),
        )

        summary = AnalysisSummary(
            total_findings=1,
            rule_based_findings=1,
            ml_predicted_findings=0,
            errors_count=0,
            warnings_count=1,
            syntax_errors_count=0,
            category_counts={"syntax_error": 1},
            severity_counts={"warning": 1},
            execution_time_ms=0.5,
            lines_analyzed=lines_count,
        )

        return AnalysisResponse(
            status="tool_unavailable",
            language=self.language_id,
            analyzer_id=self.analyzer_id,
            support_level=LanguageSupportLevel.TOOL_UNAVAILABLE.value,
            status_message=f"{self.display_name} analysis tool '{self.tool_name}' is not installed.",
            syntax_error=None,
            findings=[finding],
            summary=summary,
            server_version=self.settings.app_version,
        )

    @abstractmethod
    def analyze(
        self,
        source_code: str,
        file_path: Optional[str] = None,
    ) -> AnalysisResponse:
        """Perform static/type analysis on source code without executing it."""
        ...
