"""Tests for the TypeMind AI Machine Learning Pipeline."""

from pathlib import Path
import pytest
from app.ml.features import CodePatternFeatureExtractor
from app.ml.predictor import TypePatternPredictor
from app.ml.train import load_dataset, train_and_evaluate
from app.schemas.analysis import AnalysisRequest
from app.schemas.common import FindingOrigin
from app.services.analysis import AnalysisService


class TestFeatureExtractor:
    """Tests for deterministic AST feature extraction."""

    def test_feature_extraction_determinism(self):
        extractor = CodePatternFeatureExtractor()
        code = "def calc(a: int, b: int) -> int:\n    return a + b\n"
        f1 = extractor.extract_features(code)
        f2 = extractor.extract_features(code)

        assert f1 == f2
        assert f1["node_type"] in ("Return", "BinOp")
        assert f1["is_in_function"] == 1
        assert f1["has_return_annotation"] == 1
        assert "a" not in f1  # Variable names must NOT be features
        assert "b" not in f1

    def test_feature_extraction_malformed_input(self):
        extractor = CodePatternFeatureExtractor()
        code = "def broken(:\n"
        f = extractor.extract_features(code)

        assert f["is_malformed"] == 1
        assert f["node_type"] == "Malformed"


class TestModelTrainingAndPersistence:
    """Tests for reproducible training, evaluation, and persistence."""

    def test_dataset_loading(self):
        records = load_dataset()
        assert len(records) >= 30
        for r in records:
            assert "id" in r
            assert "code" in r
            assert "target_label" in r
            assert r["origin"] == "synthetic"

    def test_training_pipeline_execution(self, tmp_path):
        """Train model into a temporary artifact directory."""
        metadata = train_and_evaluate(artifacts_dir=tmp_path)

        assert (tmp_path / "type_classifier.joblib").exists()
        assert (tmp_path / "model_metadata.json").exists()

        assert metadata["model_name"] == "TypeMind_PatternClassifier"
        assert metadata["model_version"] == "1.0.0"
        assert "baseline_comparison" in metadata["evaluation"]
        assert "LogisticRegression" in metadata["evaluation"]["baseline_comparison"]
        assert "RandomForestClassifier" in metadata["evaluation"]["baseline_comparison"]


class TestPredictor:
    """Tests for TypePatternPredictor inference, abstention, and edge cases."""

    def test_predictor_loaded_model(self):
        predictor = TypePatternPredictor()
        assert predictor.is_available is True

        code = 'msg = "hello " + 42\n'
        res = predictor.predict(code, min_confidence=0.10)
        assert res.status == "success"
        assert res.predicted_category is not None
        assert 0.0 <= res.confidence <= 1.0
        assert len(res.probabilities) > 0
        assert len(res.features_used) > 0

    def test_predictor_abstention_on_high_threshold(self):
        predictor = TypePatternPredictor()
        code = 'x = "ambiguous"\n'
        # With threshold of 0.999, model should abstain
        res = predictor.predict(code, min_confidence=0.999)
        assert res.status == "abstain"
        assert res.reason is not None

    def test_predictor_malformed_input(self):
        predictor = TypePatternPredictor()
        res = predictor.predict("def unclosed(\n")
        assert res.status == "malformed_input"

    def test_predictor_missing_model_artifact(self, tmp_path):
        missing_model = tmp_path / "non_existent.joblib"
        predictor = TypePatternPredictor(model_path=missing_model)
        assert predictor.is_available is False

        res = predictor.predict("x = 10\n")
        assert res.status == "model_unavailable"
        assert "not been trained or loaded" in res.reason


class TestAnalysisServiceMLIntegration:
    """Tests for end-to-end integration between AST semantic rules and ML."""

    def test_ml_enabled_enriches_findings(self):
        service = AnalysisService()
        req = AnalysisRequest(
            source_code='val = "code_" + 99\n',
            enable_ml_analysis=True,
            min_confidence=0.20,
        )
        res = service.analyze_code(req)

        assert res.status == "success"
        assert len(res.findings) >= 1
        finding = res.findings[0]
        # In hybrid mode, finding has origin HYBRID and contains ml_prediction
        assert finding.origin in (FindingOrigin.HYBRID, FindingOrigin.RULE_BASED)
        if finding.origin == FindingOrigin.HYBRID:
            assert finding.ml_prediction is not None
            assert finding.ml_prediction.confidence > 0.0

    def test_ml_disabled_keeps_pure_rule_origin(self):
        service = AnalysisService()
        req = AnalysisRequest(
            source_code='val = "code_" + 99\n',
            enable_ml_analysis=False,
        )
        res = service.analyze_code(req)

        assert res.status == "success"
        assert len(res.findings) == 1
        assert res.findings[0].origin == FindingOrigin.RULE_BASED
        assert res.findings[0].ml_prediction is None
