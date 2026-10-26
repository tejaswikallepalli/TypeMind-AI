"""Diagnostic aggregator merging deterministic rule findings and ML predictions."""

from __future__ import annotations
import uuid
from typing import Dict, List, Optional, Tuple
from app.ml.predictor import MLPredictionResult
from app.schemas.common import ErrorCategory, FindingOrigin, Severity, SourceLocation
from app.schemas.diagnostics import DiagnosticFinding

CATEGORY_MAPPING = {
    "type_mismatch": ErrorCategory.TYPE_MISMATCH,
    "unsupported_operand": ErrorCategory.UNSUPPORTED_OPERAND,
    "argument_count_mismatch": ErrorCategory.ARGUMENT_COUNT_MISMATCH,
    "argument_type_mismatch": ErrorCategory.ARGUMENT_TYPE_MISMATCH,
    "incompatible_return": ErrorCategory.INCOMPATIBLE_RETURN,
    "invalid_assignment": ErrorCategory.INVALID_ASSIGNMENT,
}

SEVERITY_ORDER = {
    Severity.ERROR: 0,
    Severity.WARNING: 1,
    Severity.INFORMATION: 2,
    Severity.HINT: 3,
}


class DiagnosticAggregator:
    """Merges, corroborates, and deduplicates diagnostic findings."""

    def aggregate(
        self,
        rule_findings: List[DiagnosticFinding],
        ml_result: Optional[MLPredictionResult] = None,
        file_path: Optional[str] = None,
    ) -> List[DiagnosticFinding]:
        """Combine deterministic rule findings with ML predictions.

        Safeguards:
        - Never duplicates findings with matching location and category.
        - Never suppresses rule-based findings when ML model disagrees or abstains.
        - Upgrades matching rule findings to HYBRID when ML corroborates.
        - Pure ML predictions remain unconfirmed (is_confirmed=False).
        """
        dedup_map: Dict[Tuple[int, int, str], DiagnosticFinding] = {}

        # 1. Ingest all deterministic rule findings
        for finding in rule_findings:
            key = (
                finding.location.line,
                finding.location.column,
                finding.category.value,
            )
            # Retain first finding or higher severity if location and category collide
            if key not in dedup_map:
                dedup_map[key] = finding
            else:
                existing = dedup_map[key]
                if SEVERITY_ORDER[finding.severity] < SEVERITY_ORDER[existing.severity]:
                    dedup_map[key] = finding

        # 2. Corroborate with ML prediction if available and successful
        schema_ml_pred = ml_result.to_schema_prediction() if ml_result else None

        if schema_ml_pred and ml_result and ml_result.status == "success":
            predicted_cat = ml_result.predicted_category
            corroborated = False

            # Case A: Corroborate existing rule-based finding
            for key, finding in list(dedup_map.items()):
                # Corroborate if categories align or rule finding matches
                if finding.category.value == predicted_cat or finding.rule_id:
                    hybrid_finding = finding.model_copy(
                        update={
                            "origin": FindingOrigin.HYBRID,
                            "ml_prediction": schema_ml_pred,
                        }
                    )
                    dedup_map[key] = hybrid_finding
                    corroborated = True
                    break

            # Case B: ML predicted anomaly where rule engine found no error
            if not corroborated and not rule_findings and predicted_cat != "no_error":
                if predicted_cat in CATEGORY_MAPPING:
                    cat = CATEGORY_MAPPING[predicted_cat]
                    loc = SourceLocation(file_path=file_path, line=1, column=1)
                    ml_finding = DiagnosticFinding(
                        id=f"TM100-{uuid.uuid4().hex[:8]}",
                        message=(
                            f"Statistical code pattern analysis identified probable {predicted_cat.replace('_', ' ')} "
                            f"(model confidence: {ml_result.confidence:.0%})."
                        ),
                        category=cat,
                        severity=Severity.WARNING,
                        location=loc,
                        origin=FindingOrigin.ML_PREDICTION,
                        is_confirmed=False,  # Unconfirmed heuristic
                        rule_id="TM100_ML_PREDICTED_ANOMALY",
                        ml_prediction=schema_ml_pred,
                        explanation=(
                            f"The TypeMind ML pattern classifier detected code features associated with "
                            f"{predicted_cat}. Because this finding is statistical, developer verification is required."
                        ),
                    )
                    key = (1, 1, cat.value)
                    dedup_map[key] = ml_finding

        # 3. Sort findings stably: line asc, column asc, severity asc
        sorted_findings = sorted(
            dedup_map.values(),
            key=lambda f: (
                f.location.line,
                f.location.column,
                SEVERITY_ORDER.get(f.severity, 99),
                f.id,
            ),
        )

        return sorted_findings
