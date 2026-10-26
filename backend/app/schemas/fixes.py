"""Schemas for automated fix suggestions and code replacements."""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.common import SourceLocation


class CodeReplacement(BaseModel):
    """Specific textual edit to apply to source code."""

    location: SourceLocation = Field(..., description="Range of code to replace")
    new_text: str = Field(..., description="Replacement text")
    description: str = Field(..., description="Short explanation of this specific replacement")

    model_config = ConfigDict(frozen=True)


class SuggestedFix(BaseModel):
    """An actionable, structured recommendation to fix a diagnostic finding."""

    id: str = Field(..., description="Unique identifier for the suggested fix")
    title: str = Field(..., description="Short summary title (e.g., 'Cast argument to str()')")
    description: str = Field(..., description="Detailed explanation of why this fix resolves the issue")
    replacements: List[CodeReplacement] = Field(
        default_factory=list,
        description="List of precise code edits to apply this fix"
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score for this fix recommendation"
    )
    is_auto_applicable: bool = Field(
        default=False,
        description="True if the fix can be safely auto-applied without human inspection"
    )
    diff_preview: Optional[str] = Field(
        default=None,
        description="Optional before/after diff snippet illustrating proposed change"
    )
    requires_user_review: bool = Field(
        default=True,
        description="Indicates that developer review is required before applying fix"
    )

    model_config = ConfigDict(frozen=True)
