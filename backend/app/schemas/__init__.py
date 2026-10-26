"""TypeMind AI Schemas package.

Exports all data contracts for analysis requests, diagnostics, ML predictions,
fixes, locations, model metadata, and categories.
"""

from app.schemas.common import (
    ErrorCategory,
    FindingOrigin,
    Severity,
    SourceLocation,
    TypeInfo,
)
from app.schemas.diagnostics import (
    CategoriesResponse,
    CategoryDetail,
    DiagnosticFinding,
)
from app.schemas.fixes import CodeReplacement, SuggestedFix
from app.schemas.ml import MLPrediction, ModelInfoResponse
from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    AnalysisSummary,
)

from app.schemas.languages import (
    LanguageInfo,
    LanguageSupportLevel,
    LanguagesResponse,
)

__all__ = [
    "Severity",
    "ErrorCategory",
    "FindingOrigin",
    "SourceLocation",
    "TypeInfo",
    "DiagnosticFinding",
    "CategoryDetail",
    "CategoriesResponse",
    "CodeReplacement",
    "SuggestedFix",
    "MLPrediction",
    "ModelInfoResponse",
    "AnalysisRequest",
    "AnalysisResponse",
    "AnalysisSummary",
    "LanguageInfo",
    "LanguageSupportLevel",
    "LanguagesResponse",
]
