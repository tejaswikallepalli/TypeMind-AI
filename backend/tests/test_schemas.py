"""Tests for core data contracts, Pydantic schemas, and validation safeguards."""

import pytest
from pydantic import ValidationError

from app.schemas.analysis import AnalysisRequest, AnalysisResponse, AnalysisSummary
from app.schemas.common import (
    ErrorCategory,
    FindingOrigin,
    Severity,
    SourceLocation,
    TypeInfo,
)
from app.schemas.diagnostics import DiagnosticFinding
from app.schemas.fixes import CodeReplacement, SuggestedFix
from app.schemas.ml import MLPrediction


class TestSourceLocation:
    """Tests for SourceLocation coordinate validation."""

    def test_valid_location(self):
        loc = SourceLocation(file_path="main.py", line=10, column=5, end_line=10, end_column=15)
        assert loc.line == 10
        assert loc.column == 5
        assert loc.end_line == 10
        assert loc.end_column == 15

    def test_invalid_zero_line(self):
        with pytest.raises(ValidationError):
            SourceLocation(line=0, column=1)

    def test_invalid_zero_column(self):
        with pytest.raises(ValidationError):
            SourceLocation(line=1, column=0)

    def test_invalid_end_line_before_start_line(self):
        with pytest.raises(ValidationError) as exc:
            SourceLocation(line=10, column=5, end_line=9, end_column=5)
        assert "end_line cannot be less than start line" in str(exc.value)

    def test_invalid_end_column_before_start_column_on_same_line(self):
        with pytest.raises(ValidationError) as exc:
            SourceLocation(line=10, column=10, end_line=10, end_column=5)
        assert "end_column cannot be less than start column" in str(exc.value)


class TestTypeInfo:
    """Tests for TypeInfo schema."""

    def test_valid_type_info(self):
        t = TypeInfo(raw_type="List[str]", is_inferred=True, type_args=["str"], confidence=0.95)
        assert t.raw_type == "List[str]"
        assert t.is_inferred is True
        assert t.confidence == 0.95

    def test_invalid_confidence_out_of_bounds(self):
        with pytest.raises(ValidationError):
            TypeInfo(raw_type="int", confidence=1.5)


class TestMLPrediction:
    """Tests for MLPrediction schema."""

    def test_valid_ml_prediction(self):
        pred = MLPrediction(
            predicted_error_type="type_mismatch",
            confidence=0.88,
            model_name="random_forest_type_v1",
            model_version="1.0.0",
            probabilities={"type_mismatch": 0.88, "none_safety": 0.12},
            features_used=["ast_binop_add", "left_type_str", "right_type_int"],
        )
        assert pred.confidence == 0.88
        assert pred.model_name == "random_forest_type_v1"

    def test_invalid_ml_confidence_negative(self):
        with pytest.raises(ValidationError):
            MLPrediction(
                predicted_error_type="type_mismatch",
                confidence=-0.1,
                model_name="model_v1",
            )


class TestDiagnosticFinding:
    """Tests for DiagnosticFinding and rule vs ML segregation."""

    def test_valid_confirmed_rule_based_finding(self):
        finding = DiagnosticFinding(
            id="rule-finding-001",
            message="Unsupported operand types for +: 'str' and 'int'",
            category=ErrorCategory.UNSUPPORTED_OPERAND,
            severity=Severity.ERROR,
            location=SourceLocation(line=5, column=12),
            origin=FindingOrigin.RULE_BASED,
            is_confirmed=True,
            rule_id="TM005_UNSUPPORTED_OPERAND",
            expected_type=TypeInfo(raw_type="str"),
            observed_type=TypeInfo(raw_type="int"),
            suggested_fixes=[
                SuggestedFix(
                    id="fix-001",
                    title="Convert int to str",
                    description="Wrap the integer with str()",
                    replacements=[
                        CodeReplacement(
                            location=SourceLocation(line=5, column=12, end_line=5, end_column=15),
                            new_text="str(count)",
                            description="Apply str() cast",
                        )
                    ],
                    confidence=0.99,
                    is_auto_applicable=True,
                )
            ],
        )
        assert finding.origin == FindingOrigin.RULE_BASED
        assert finding.is_confirmed is True
        assert len(finding.suggested_fixes) == 1

    def test_valid_ml_prediction_finding_unconfirmed(self):
        finding = DiagnosticFinding(
            id="ml-finding-001",
            message="Probable None dereference inferred from variable flow",
            category=ErrorCategory.NONE_SAFETY,
            severity=Severity.WARNING,
            location=SourceLocation(line=12, column=8),
            origin=FindingOrigin.ML_PREDICTION,
            is_confirmed=False,  # Correct: pure ML prediction is not confirmed
            ml_prediction=MLPrediction(
                predicted_error_type="none_safety",
                confidence=0.74,
                model_name="gradient_boost_v1",
            ),
        )
        assert finding.origin == FindingOrigin.ML_PREDICTION
        assert finding.is_confirmed is False
        assert finding.ml_prediction is not None

    def test_reject_ml_prediction_without_ml_payload(self):
        """ML findings must provide MLPrediction payload."""
        with pytest.raises(ValidationError) as exc:
            DiagnosticFinding(
                id="ml-invalid-001",
                message="Probable type error",
                category=ErrorCategory.TYPE_MISMATCH,
                severity=Severity.WARNING,
                location=SourceLocation(line=1, column=1),
                origin=FindingOrigin.ML_PREDICTION,
                is_confirmed=False,
                ml_prediction=None,
            )
        assert "must include an ml_prediction payload" in str(exc.value)

    def test_reject_pure_ml_prediction_marked_as_confirmed_without_evidence(self):
        """Pure ML predictions cannot be marked is_confirmed=True without rule evidence."""
        with pytest.raises(ValidationError) as exc:
            DiagnosticFinding(
                id="ml-invalid-002",
                message="Predicted error falsely marked as confirmed",
                category=ErrorCategory.TYPE_MISMATCH,
                severity=Severity.ERROR,
                location=SourceLocation(line=1, column=1),
                origin=FindingOrigin.ML_PREDICTION,
                is_confirmed=True,  # INVALID: cannot confirm ML without rule evidence
                ml_prediction=MLPrediction(
                    predicted_error_type="type_mismatch",
                    confidence=0.85,
                    model_name="model_v1",
                ),
                rule_id=None,
            )
        assert "cannot be marked as confirmed" in str(exc.value)


class TestAnalysisContracts:
    """Tests for AnalysisRequest, AnalysisSummary, and AnalysisResponse."""

    def test_valid_analysis_request(self):
        req = AnalysisRequest(
            source_code="x: int = 'hello'\n",
            file_path="test.py",
            enable_ml_analysis=True,
            min_confidence=0.7,
        )
        assert req.source_code.strip() == "x: int = 'hello'"
        assert req.min_confidence == 0.7

    def test_reject_empty_source_code(self):
        with pytest.raises(ValidationError):
            AnalysisRequest(source_code="")

    def test_valid_analysis_response(self):
        summary = AnalysisSummary(
            total_findings=1,
            rule_based_findings=1,
            ml_predicted_findings=0,
            errors_count=1,
            warnings_count=0,
            execution_time_ms=12.5,
            lines_analyzed=10,
        )
        resp = AnalysisResponse(
            status="success",
            findings=[],
            summary=summary,
            server_version="0.1.0",
        )
        assert resp.status == "success"
        assert resp.summary.total_findings == 1
        assert resp.server_version == "0.1.0"
