"""Automated test suite for TypeMind AI Diagnostic Intelligence Layer."""

import json
from app.diagnostics.aggregator import DiagnosticAggregator
from app.diagnostics.explainer import DiagnosticExplainer
from app.diagnostics.fix_generator import FixGenerator
from app.diagnostics.service import DiagnosticIntelligenceService
from app.ml.predictor import MLPredictionResult
from app.schemas.analysis import AnalysisRequest, AnalysisResponse, AnalysisSummary
from app.schemas.common import ErrorCategory, FindingOrigin, Severity, SourceLocation, TypeInfo
from app.schemas.diagnostics import DiagnosticFinding
from app.schemas.fixes import CodeReplacement, SuggestedFix
from app.services.analysis import AnalysisService


class TestDiagnosticDeduplicationAndAggregation:
    """Tests for finding deduplication, conflict resolution, and provenance tracking."""

    def test_duplicate_findings_at_same_location_deduplicated(self):
        aggregator = DiagnosticAggregator()
        f1 = DiagnosticFinding(
            id="f1",
            message="Type mismatch in addition",
            category=ErrorCategory.TYPE_MISMATCH,
            severity=Severity.ERROR,
            location=SourceLocation(line=5, column=10),
            origin=FindingOrigin.RULE_BASED,
            is_confirmed=True,
            rule_id="TM001_STRING_NUMBER_CONCAT",
        )
        f2 = DiagnosticFinding(
            id="f2",
            message="Duplicate finding at same location",
            category=ErrorCategory.TYPE_MISMATCH,
            severity=Severity.ERROR,
            location=SourceLocation(line=5, column=10),
            origin=FindingOrigin.RULE_BASED,
            is_confirmed=True,
            rule_id="TM001_STRING_NUMBER_CONCAT",
        )

        merged = aggregator.aggregate(rule_findings=[f1, f2])
        assert len(merged) == 1
        assert merged[0].id == "f1"

    def test_higher_severity_prioritized_on_conflict(self):
        aggregator = DiagnosticAggregator()
        f_warn = DiagnosticFinding(
            id="f_warn",
            message="Warning on assignment",
            category=ErrorCategory.TYPE_MISMATCH,
            severity=Severity.WARNING,
            location=SourceLocation(line=3, column=5),
            origin=FindingOrigin.RULE_BASED,
            is_confirmed=True,
            rule_id="TM007_INCOMPATIBLE_REASSIGNMENT",
        )
        f_err = DiagnosticFinding(
            id="f_err",
            message="Error on assignment",
            category=ErrorCategory.TYPE_MISMATCH,
            severity=Severity.ERROR,
            location=SourceLocation(line=3, column=5),
            origin=FindingOrigin.RULE_BASED,
            is_confirmed=True,
            rule_id="TM006_INVALID_ANNOTATED_ASSIGNMENT",
        )

        merged = aggregator.aggregate(rule_findings=[f_warn, f_err])
        assert len(merged) == 1
        assert merged[0].severity == Severity.ERROR
        assert merged[0].id == "f_err"

    def test_rule_finding_never_suppressed_when_ml_disagrees(self):
        aggregator = DiagnosticAggregator()
        rule_f = DiagnosticFinding(
            id="rule_01",
            message="Argument count mismatch",
            category=ErrorCategory.ARGUMENT_COUNT_MISMATCH,
            severity=Severity.ERROR,
            location=SourceLocation(line=8, column=4),
            origin=FindingOrigin.RULE_BASED,
            is_confirmed=True,
            rule_id="TM003_ARGUMENT_COUNT_MISMATCH",
        )
        # ML predicts a different category
        ml_res = MLPredictionResult(
            status="success",
            predicted_category="incompatible_return",
            confidence=0.85,
            probabilities={"incompatible_return": 0.85},
            features_used=["node_type=Call"],
        )

        merged = aggregator.aggregate(rule_findings=[rule_f], ml_result=ml_res)
        assert len(merged) == 1
        # Rule finding is preserved and marked HYBRID with the prediction attached
        assert merged[0].id == "rule_01"
        assert merged[0].category == ErrorCategory.ARGUMENT_COUNT_MISMATCH


class TestFixGenerator:
    """Tests for structured fix suggestion generation."""

    def test_string_concat_fix_generation(self):
        generator = FixGenerator()
        code = 'greeting = "User ID: " + user_id\n'
        loc = SourceLocation(line=1, column=26, end_line=1, end_column=33)
        fixes = generator.generate_fixes(
            rule_id="TM001_STRING_NUMBER_CONCAT",
            location=loc,
            source_code=code,
            expected_type=TypeInfo(raw_type="str"),
            observed_type=TypeInfo(raw_type="int"),
        )

        assert len(fixes) >= 1
        fix = fixes[0]
        assert "str(" in fix.replacements[0].new_text
        assert fix.diff_preview is not None
        assert "- user_id" in fix.diff_preview
        assert "+ str(user_id)" in fix.diff_preview
        assert fix.requires_user_review is True
        assert fix.is_auto_applicable is False  # Never claims guaranteed fix

    def test_incompatible_return_fix_generation(self):
        generator = FixGenerator()
        code = "def get_ratio() -> float:\n    return '1.5'\n"
        loc = SourceLocation(line=2, column=12, end_line=2, end_column=17)
        fixes = generator.generate_fixes(
            rule_id="TM005_INCOMPATIBLE_RETURN",
            location=loc,
            source_code=code,
            expected_type=TypeInfo(raw_type="float"),
            observed_type=TypeInfo(raw_type="str"),
        )

        assert len(fixes) >= 1
        assert "float('1.5')" in fixes[0].replacements[0].new_text


class TestDiagnosticExplainer:
    """Tests for plain-language educational explanations and provenance disclosures."""

    def test_explainer_with_known_types(self):
        explainer = DiagnosticExplainer()
        exp = explainer.explain(
            message="Cannot concatenate str and int",
            category=ErrorCategory.TYPE_MISMATCH,
            origin=FindingOrigin.RULE_BASED,
            expected_type=TypeInfo(raw_type="str"),
            observed_type=TypeInfo(raw_type="int"),
            rule_id="TM001_STRING_NUMBER_CONCAT",
        )
        assert "Expected type 'str', but observed 'int'." in exp
        assert "Deterministically verified by AST semantic checking rules." in exp

    def test_explainer_with_unknown_types_avoids_manufacturing_types(self):
        explainer = DiagnosticExplainer()
        exp = explainer.explain(
            message="Uncertain expression",
            category=ErrorCategory.TYPE_MISMATCH,
            origin=FindingOrigin.RULE_BASED,
            expected_type=None,
            observed_type=None,
        )
        assert "Specific type annotations are not available" in exp
        assert "Expected type" not in exp


class TestDiagnosticIntelligenceService:
    """Tests for service-level grouped metrics and serialization."""

    def test_grouped_metrics_calculation(self):
        service = DiagnosticIntelligenceService()
        source = 'a = "code_" + 10\nb = [1, 2] - [1]\n'
        base_resp = AnalysisResponse(
            status="success",
            findings=[
                DiagnosticFinding(
                    id="f1",
                    message="Concat error",
                    category=ErrorCategory.TYPE_MISMATCH,
                    severity=Severity.ERROR,
                    location=SourceLocation(line=1, column=5),
                    origin=FindingOrigin.RULE_BASED,
                    is_confirmed=True,
                    rule_id="TM001_STRING_NUMBER_CONCAT",
                ),
                DiagnosticFinding(
                    id="f2",
                    message="Arithmetic warning",
                    category=ErrorCategory.UNSUPPORTED_OPERAND,
                    severity=Severity.WARNING,
                    location=SourceLocation(line=2, column=5),
                    origin=FindingOrigin.RULE_BASED,
                    is_confirmed=True,
                    rule_id="TM002_UNSUPPORTED_ARITHMETIC",
                ),
            ],
            summary=AnalysisSummary(total_findings=2, lines_analyzed=2),
            server_version="0.1.0",
        )

        final_resp = service.process_diagnostics(base_resp, source_code=source)
        summary = final_resp.summary

        assert summary.total_findings == 2
        assert summary.errors_count == 1
        assert summary.warnings_count == 1
        assert summary.category_counts.get("type_mismatch") == 1
        assert summary.category_counts.get("unsupported_operand") == 1
        assert summary.severity_counts.get("error") == 1
        assert summary.severity_counts.get("warning") == 1

    def test_diagnostic_json_serialization(self):
        service = AnalysisService()
        req = AnalysisRequest(
            source_code='def check(x: int) -> int:\n    return x + "10"\n',
            enable_ml_analysis=True,
        )
        resp = service.analyze_code(req)

        # Ensure complete JSON roundtrip
        json_data = resp.model_dump_json()
        assert isinstance(json_data, str)
        parsed = json.loads(json_data)
        assert parsed["status"] == "success"
        assert len(parsed["findings"]) >= 1
        assert "category_counts" in parsed["summary"]
        assert "severity_counts" in parsed["summary"]
