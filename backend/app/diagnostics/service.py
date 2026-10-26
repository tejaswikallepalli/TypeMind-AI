"""Diagnostic intelligence service orchestrating aggregation, explanation, and fix generation."""

from __future__ import annotations
from typing import Dict, List, Optional
from app.diagnostics.aggregator import DiagnosticAggregator
from app.diagnostics.explainer import DiagnosticExplainer
from app.diagnostics.fix_generator import FixGenerator
from app.ml.predictor import MLPredictionResult
from app.schemas.analysis import AnalysisResponse, AnalysisSummary
from app.schemas.common import FindingOrigin, Severity
from app.schemas.diagnostics import DiagnosticFinding


class DiagnosticIntelligenceService:
    """Combines rule findings, ML inference, educational explanations, and fix suggestions."""

    def __init__(self) -> None:
        self.aggregator = DiagnosticAggregator()
        self.explainer = DiagnosticExplainer()
        self.fix_generator = FixGenerator()

    def process_diagnostics(
        self,
        base_response: AnalysisResponse,
        source_code: str,
        ml_result: Optional[MLPredictionResult] = None,
        file_path: Optional[str] = None,
    ) -> AnalysisResponse:
        """Merge rule findings and ML predictions into enriched, deduplicated diagnostics."""
        # Syntax error halts semantic processing
        if base_response.status == "syntax_error":
            return base_response

        # 1. Aggregate and deduplicate findings
        merged_findings = self.aggregator.aggregate(
            rule_findings=base_response.findings,
            ml_result=ml_result,
            file_path=file_path,
        )

        # 2. Enrich findings with comprehensive explanations and fix suggestions
        enriched_findings: List[DiagnosticFinding] = []
        for finding in merged_findings:
            # Generate or preserve suggested fixes
            fixes = finding.suggested_fixes
            if not fixes and finding.rule_id:
                fixes = self.fix_generator.generate_fixes(
                    rule_id=finding.rule_id,
                    location=finding.location,
                    source_code=source_code,
                    expected_type=finding.expected_type,
                    observed_type=finding.observed_type,
                )

            # Generate enriched plain-language explanation
            explanation = self.explainer.explain(
                message=finding.message,
                category=finding.category,
                origin=finding.origin,
                expected_type=finding.expected_type,
                observed_type=finding.observed_type,
                ml_prediction=finding.ml_prediction,
                rule_id=finding.rule_id,
            )

            enriched = finding.model_copy(
                update={
                    "explanation": explanation,
                    "suggested_fixes": fixes,
                }
            )
            enriched_findings.append(enriched)

        # 3. Compute grouped metrics by category and severity
        category_counts: Dict[str, int] = {}
        severity_counts: Dict[str, int] = {}
        rule_count = 0
        ml_count = 0

        for f in enriched_findings:
            cat_name = f.category.value
            sev_name = f.severity.value
            category_counts[cat_name] = category_counts.get(cat_name, 0) + 1
            severity_counts[sev_name] = severity_counts.get(sev_name, 0) + 1

            if f.origin == FindingOrigin.RULE_BASED:
                rule_count += 1
            elif f.origin == FindingOrigin.ML_PREDICTION:
                ml_count += 1
            elif f.origin == FindingOrigin.HYBRID:
                rule_count += 1
                ml_count += 1

        summary = base_response.summary.model_copy(
            update={
                "total_findings": len(enriched_findings),
                "rule_based_findings": rule_count,
                "ml_predicted_findings": ml_count,
                "errors_count": severity_counts.get(Severity.ERROR.value, 0),
                "warnings_count": severity_counts.get(Severity.WARNING.value, 0),
                "category_counts": category_counts,
                "severity_counts": severity_counts,
            }
        )

        return base_response.model_copy(
            update={
                "findings": enriched_findings,
                "summary": summary,
            }
        )


_diagnostic_service = DiagnosticIntelligenceService()


def get_diagnostic_service() -> DiagnosticIntelligenceService:
    """Return singleton DiagnosticIntelligenceService instance."""
    return _diagnostic_service
