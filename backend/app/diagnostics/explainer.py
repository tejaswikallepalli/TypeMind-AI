"""Plain-language educational diagnostic explanations and provenance reporting."""

from __future__ import annotations
from typing import Optional
from app.schemas.common import ErrorCategory, FindingOrigin, TypeInfo
from app.schemas.ml import MLPrediction


class DiagnosticExplainer:
    """Generates plain-language explanations tailored for developers."""

    def explain(
        self,
        message: str,
        category: ErrorCategory,
        origin: FindingOrigin,
        expected_type: Optional[TypeInfo] = None,
        observed_type: Optional[TypeInfo] = None,
        ml_prediction: Optional[MLPrediction] = None,
        rule_id: Optional[str] = None,
    ) -> str:
        """Compose a comprehensive, readable explanation for a diagnostic finding."""
        parts = []

        # 1. Plain-language category context
        category_explanations = {
            ErrorCategory.TYPE_MISMATCH: (
                "An expression combines incompatible data types where Python requires matching "
                "or explicitly convertible types."
            ),
            ErrorCategory.UNSUPPORTED_OPERAND: (
                "The requested operator is not implemented for the specified operand types. "
                "Python does not support arithmetic or sequence operations across these types."
            ),
            ErrorCategory.ARGUMENT_COUNT_MISMATCH: (
                "The number of positional arguments provided does not match the parameters "
                "defined in the function signature."
            ),
            ErrorCategory.ARGUMENT_TYPE_MISMATCH: (
                "An argument provided to the function call does not conform to the parameter's "
                "declared type annotation."
            ),
            ErrorCategory.INCOMPATIBLE_RETURN: (
                "The value returned by this function conflicts with the return type annotation "
                "declared in the function header."
            ),
            ErrorCategory.INVALID_ASSIGNMENT: (
                "A variable with an explicit type annotation was assigned an expression of "
                "an incompatible type."
            ),
            ErrorCategory.SYNTAX_ERROR: (
                "The source code contains invalid Python syntax and cannot be parsed into an Abstract Syntax Tree."
            ),
        }

        base_explanation = category_explanations.get(category, message)
        parts.append(base_explanation)

        # 2. Type resolution details (only when known, never manufactured)
        if expected_type and observed_type:
            parts.append(
                f"Expected type '{expected_type.raw_type}', but observed '{observed_type.raw_type}'."
            )
        elif expected_type:
            parts.append(f"Expected type '{expected_type.raw_type}'.")
        elif observed_type:
            parts.append(f"Observed type '{observed_type.raw_type}'.")
        else:
            parts.append("Specific type annotations are not available for this expression.")

        # 3. Provenance and Confidence Disclosure
        if origin == FindingOrigin.RULE_BASED:
            parts.append("Provenance: Deterministically verified by AST semantic checking rules.")
        elif origin == FindingOrigin.HYBRID and ml_prediction:
            parts.append(
                f"Provenance: Confirmed by static AST rules and corroborated by "
                f"TypeMind ML classifier ({ml_prediction.model_name} v{ml_prediction.model_version}) "
                f"with {ml_prediction.confidence:.0%} confidence."
            )
        elif origin == FindingOrigin.ML_PREDICTION and ml_prediction:
            parts.append(
                f"Provenance: Probabilistic heuristic detected by ML classifier "
                f"with {ml_prediction.confidence:.0%} confidence. This finding is unconfirmed "
                f"by static rules and should be verified by developer inspection."
            )

        return " ".join(parts)
