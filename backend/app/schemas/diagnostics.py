"""Diagnostic finding schemas and domain integrity validators."""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.common import ErrorCategory, FindingOrigin, Severity, SourceLocation, TypeInfo
from app.schemas.fixes import SuggestedFix
from app.schemas.ml import MLPrediction


class DiagnosticFinding(BaseModel):
    """Core diagnostic finding representing a detected type anomaly or warning.

    Crucially distinguishes confirmed deterministic rule-based errors from
    probabilistic machine learning predictions.
    """

    id: str = Field(..., description="Unique deterministic or generated diagnostic ID")
    message: str = Field(..., description="Human-readable summary of the detected issue")
    category: ErrorCategory = Field(..., description="Classified type error category")
    severity: Severity = Field(default=Severity.ERROR, description="Diagnostic severity level")
    location: SourceLocation = Field(..., description="Code coordinates of the finding")

    # Origin & Confirmation Status
    origin: FindingOrigin = Field(
        ...,
        description="Origin of finding: RULE_BASED (deterministic), ML_PREDICTION (probabilistic), or HYBRID"
    )
    is_confirmed: bool = Field(
        default=False,
        description="True ONLY if deterministically verified. Never True for pure ML predictions without rule evidence."
    )

    # Detailed Type Analysis
    expected_type: Optional[TypeInfo] = Field(default=None, description="Expected type at this location, if known")
    observed_type: Optional[TypeInfo] = Field(default=None, description="Observed/inferred type at this location, if known")

    # ML Inference Details
    ml_prediction: Optional[MLPrediction] = Field(
        default=None,
        description="Machine learning inference details if this finding originated or was enriched by ML"
    )

    # Rule and Fix metadata
    rule_id: Optional[str] = Field(default=None, description="Static rule code, e.g. 'TM001_TYPE_MISMATCH'")
    suggested_fixes: List[SuggestedFix] = Field(
        default_factory=list,
        description="List of proposed automated or manual code fixes"
    )
    explanation: Optional[str] = Field(
        default=None,
        description="Detailed contextual explanation to assist developer understanding"
    )

    model_config = ConfigDict(frozen=True)

    @model_validator(mode="after")
    def validate_ml_and_rule_integrity(self) -> "DiagnosticFinding":
        """Enforce domain contracts:
        1. Pure ML predictions MUST attach MLPrediction metadata.
        2. Pure ML predictions MUST NEVER be marked is_confirmed=True without deterministic rule evidence.
        3. Rule-based findings should default or be confirmed when verified by static rules.
        """
        if self.origin == FindingOrigin.ML_PREDICTION:
            if self.ml_prediction is None:
                raise ValueError("Findings with origin 'ml_prediction' must include an ml_prediction payload")
            if self.is_confirmed and not self.rule_id:
                raise ValueError(
                    "Pure ML predictions cannot be marked as confirmed (is_confirmed=True) "
                    "without supporting deterministic rule evidence (rule_id)."
                )

        if self.origin == FindingOrigin.RULE_BASED:
            # Rule based findings should not have ML-only status
            pass

        return self


class CategoryDetail(BaseModel):
    """Detailed metadata describing a recognized diagnostic category."""

    code: str = Field(..., description="Canonical category key (e.g. 'type_mismatch')")
    title: str = Field(..., description="Human-readable title")
    description: str = Field(..., description="Detailed explanation of what this category identifies")
    default_severity: Severity = Field(..., description="Default diagnostic severity")
    rule_ids: List[str] = Field(default_factory=list, description="Associated rule IDs")
    fix_support: bool = Field(default=False, description="True if automated fix generation is available")

    model_config = ConfigDict(frozen=True)


class CategoriesResponse(BaseModel):
    """Response containing all registered diagnostic categories."""

    categories: List[CategoryDetail] = Field(..., description="List of recognized diagnostic categories")
    total_categories: int = Field(..., ge=0, description="Total number of categories available")

    model_config = ConfigDict(frozen=True)
