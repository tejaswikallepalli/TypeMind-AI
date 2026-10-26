"""Schemas for source code analysis requests, diagnostic summaries, and API responses."""

from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.diagnostics import DiagnosticFinding


class AnalysisRequest(BaseModel):
    """Payload sent by client to request semantic type analysis of Python source code."""

    source_code: str = Field(
        ...,
        min_length=1,
        max_length=500_000,
        description="Raw Python source code to analyze (max 500KB)"
    )
    file_path: Optional[str] = Field(
        default=None,
        description="Optional file name or relative path to provide context"
    )
    language: Optional[str] = Field(
        default=None,
        description="Target programming language for analysis (e.g. 'python', 'typescript', 'java', 'c', 'cpp', 'go', 'rust'). Defaults to Python or inferred from file_path."
    )
    python_version: str = Field(
        default="3.12",
        description="Target Python version grammar for semantic analysis (when language='python')"
    )
    enable_ml_analysis: bool = Field(
        default=True,
        description="Whether to run the ML classifier in addition to static AST rules (Python only)"
    )
    min_confidence: float = Field(
        default=0.60,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for reporting ML predictions"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source_code": "def greet(name: str) -> str:\n    return name + 123\n",
                "file_path": "example.py",
                "language": "python",
                "python_version": "3.12",
                "enable_ml_analysis": True,
                "min_confidence": 0.60
            }
        }
    )


class AnalysisSummary(BaseModel):
    """Summary metrics of the completed source code analysis."""

    total_findings: int = Field(default=0, ge=0, description="Total number of findings detected")
    rule_based_findings: int = Field(default=0, ge=0, description="Count of confirmed rule-based findings")
    ml_predicted_findings: int = Field(default=0, ge=0, description="Count of probabilistic ML predictions")
    errors_count: int = Field(default=0, ge=0, description="Findings with severity ERROR")
    warnings_count: int = Field(default=0, ge=0, description="Findings with severity WARNING")
    syntax_errors_count: int = Field(default=0, ge=0, description="Syntax errors detected")
    category_counts: Dict[str, int] = Field(default_factory=dict, description="Findings grouped by error category")
    severity_counts: Dict[str, int] = Field(default_factory=dict, description="Findings grouped by severity")
    execution_time_ms: float = Field(default=0.0, ge=0.0, description="Analysis execution time in milliseconds")
    lines_analyzed: int = Field(default=0, ge=0, description="Total non-empty lines of code parsed")

    model_config = ConfigDict(frozen=True)


class AnalysisResponse(BaseModel):
    """Structured response returned by the analysis API endpoint."""

    status: str = Field(
        default="success",
        description="Status of the analysis: 'success', 'syntax_error', 'partial', 'tool_unavailable', or 'error'"
    )
    language: str = Field(
        default="python",
        description="Programming language analyzed"
    )
    analyzer_id: str = Field(
        default="python_ast_semantic",
        description="Identifier of the executing analyzer adapter"
    )
    support_level: str = Field(
        default="supported",
        description="Support level: 'supported', 'partial', or 'tool_unavailable'"
    )
    status_message: Optional[str] = Field(
        default=None,
        description="Detailed message, warning, or setup instructions"
    )
    syntax_error: Optional[DiagnosticFinding] = Field(
        default=None,
        description="Syntax error finding if source code failed to parse, separated from semantic findings"
    )
    findings: List[DiagnosticFinding] = Field(
        default_factory=list,
        description="List of detected semantic diagnostic findings"
    )
    summary: AnalysisSummary = Field(..., description="Aggregated metric summary of the analysis")
    server_version: str = Field(..., description="Version of the TypeMind AI engine")

    model_config = ConfigDict(frozen=True)

