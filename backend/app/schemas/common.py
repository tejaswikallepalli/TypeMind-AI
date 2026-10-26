"""Common schemas, enums, and location contracts."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Severity(str, Enum):
    """Diagnostic severity level."""

    ERROR = "error"
    WARNING = "warning"
    INFORMATION = "information"
    HINT = "hint"


class ErrorCategory(str, Enum):
    """Categorization of detected semantic and type anomalies."""

    TYPE_MISMATCH = "type_mismatch"
    ATTRIBUTE_NOT_FOUND = "attribute_not_found"
    INCOMPATIBLE_RETURN = "incompatible_return"
    ARGUMENT_COUNT_MISMATCH = "argument_count_mismatch"
    ARGUMENT_TYPE_MISMATCH = "argument_type_mismatch"
    UNSUPPORTED_OPERAND = "unsupported_operand"
    UNDEFINED_NAME = "undefined_name"
    NONE_SAFETY = "none_safety"
    INVALID_ASSIGNMENT = "invalid_assignment"
    SYNTAX_ERROR = "syntax_error"
    OTHER = "other"


class FindingOrigin(str, Enum):
    """Distinguishes deterministic rule-based checks from probabilistic ML predictions.

    - RULE_BASED: Deterministically proven by AST analysis, symbol resolution, or type checking rules.
    - ML_PREDICTION: Inferred probabilistically by machine learning classifier.
    - HYBRID: Detected via rule heuristics and re-scored or corroborated by ML.
    """

    RULE_BASED = "rule_based"
    ML_PREDICTION = "ml_prediction"
    HYBRID = "hybrid"


class SourceLocation(BaseModel):
    """Precise source code coordinate for a diagnostic finding."""

    file_path: Optional[str] = Field(default=None, description="Path to file being analyzed, if applicable")
    line: int = Field(..., ge=1, description="1-indexed line number where the issue starts")
    column: int = Field(..., ge=1, description="1-indexed column offset where the issue starts")
    end_line: Optional[int] = Field(default=None, ge=1, description="1-indexed end line number")
    end_column: Optional[int] = Field(default=None, ge=1, description="1-indexed end column offset")

    model_config = ConfigDict(frozen=True)

    @model_validator(mode="after")
    def validate_range(self) -> "SourceLocation":
        """Ensure end location is not before start location."""
        if self.end_line is not None:
            if self.end_line < self.line:
                raise ValueError("end_line cannot be less than start line")
            if self.end_line == self.line and self.end_column is not None and self.end_column < self.column:
                raise ValueError("end_column cannot be less than start column on the same line")
        return self


class TypeInfo(BaseModel):
    """Structured representation of observed and expected types."""

    raw_type: str = Field(..., description="Stringified type name, e.g. 'str', 'int', 'List[int]'")
    is_inferred: bool = Field(default=False, description="True if type was statically inferred rather than annotated")
    type_args: List[str] = Field(default_factory=list, description="Generic arguments if present, e.g. ['int'] in List[int]")
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Confidence of type inference if probabilistic")
    notes: Optional[str] = Field(default=None, description="Additional context or notes regarding type resolution")

    model_config = ConfigDict(frozen=True)
