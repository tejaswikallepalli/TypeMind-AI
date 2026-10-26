"""ML inference engine, model loader, and abstention handler."""

from __future__ import annotations
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import joblib

from app.core.config import get_settings
from app.ml.features import CodePatternFeatureExtractor
from app.schemas.ml import MLPrediction

logger = logging.getLogger("typemind.ml")

DEFAULT_MODEL_DIR = Path(__file__).resolve().parent / "artifacts"
DEFAULT_MODEL_PATH = DEFAULT_MODEL_DIR / "type_classifier.joblib"
DEFAULT_METADATA_PATH = DEFAULT_MODEL_DIR / "model_metadata.json"


@dataclass
class MLPredictionResult:
    """Internal domain result from the ML classifier."""

    status: str  # "success", "abstain", "uncertain", "malformed_input", "model_unavailable"
    predicted_category: Optional[str] = None
    confidence: float = 0.0
    probabilities: Dict[str, float] = field(default_factory=dict)
    model_name: str = "TypeMind_PatternClassifier"
    model_version: str = "1.0.0"
    features_used: List[str] = field(default_factory=list)
    reason: Optional[str] = None

    def to_schema_prediction(self) -> Optional[MLPrediction]:
        """Convert to Phase 1 Pydantic MLPrediction schema if prediction is valid."""
        if self.status != "success" or not self.predicted_category:
            return None
        return MLPrediction(
            predicted_error_type=self.predicted_category,
            confidence=round(self.confidence, 4),
            model_name=self.model_name,
            model_version=self.model_version,
            probabilities={k: round(v, 4) for k, v in self.probabilities.items()},
            features_used=self.features_used,
            notes=self.reason,
        )


class TypePatternPredictor:
    """Production ML predictor with abstention, feature tracking, and graceful fallback."""

    def __init__(
        self,
        model_path: Optional[Path] = None,
        metadata_path: Optional[Path] = None,
    ) -> None:
        self.settings = get_settings()
        self.model_path = model_path or DEFAULT_MODEL_PATH
        self.metadata_path = metadata_path or DEFAULT_METADATA_PATH
        self.extractor = CodePatternFeatureExtractor()
        self.pipeline: Optional[Any] = None
        self.metadata: Dict[str, Any] = {}
        self._load_model_artifacts()

    def _load_model_artifacts(self) -> None:
        """Attempt to load fitted pipeline and metadata. Logs warning if missing."""
        if not self.model_path.exists():
            logger.warning("ML model artifact not found at %s. Predictor will abstain.", self.model_path)
            self.pipeline = None
            return

        try:
            self.pipeline = joblib.load(self.model_path)
            if self.metadata_path.exists():
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
            logger.info("Loaded ML model artifact successfully from %s", self.model_path)
        except Exception as e:
            logger.error("Failed to load ML model artifact: %s", str(e), exc_info=True)
            self.pipeline = None

    @property
    def is_available(self) -> bool:
        """True if the model artifact is loaded and ready for inference."""
        return self.pipeline is not None

    def predict(
        self,
        source_code: str,
        min_confidence: Optional[float] = None,
    ) -> MLPredictionResult:
        """Classify a Python code snippet.

        Returns an explicit abstention/uncertain result when confidence is below threshold
        or when the input is malformed.
        """
        threshold = (
            min_confidence
            if min_confidence is not None
            else self.settings.min_confidence_threshold
        )

        if not self.is_available:
            return MLPredictionResult(
                status="model_unavailable",
                reason="Model artifact has not been trained or loaded.",
            )

        # Extract features
        features = self.extractor.extract_features(source_code)
        if features.get("is_malformed"):
            return MLPredictionResult(
                status="malformed_input",
                reason="Source code contains syntax errors and cannot be featurized.",
            )

        try:
            # Predict probabilities
            probs = self.pipeline.predict_proba([features])[0]
            classes = self.pipeline.classes_

            prob_dict = {str(cls): float(p) for cls, p in zip(classes, probs)}
            best_idx = int(probs.argmax())
            best_class = str(classes[best_idx])
            best_prob = float(probs[best_idx])

            # Key active features for explainability
            active_features = [
                f"{k}={v}" for k, v in features.items()
                if v not in (0, "n/a", "None")
            ][:5]

            # Abstention rule: explicit uncertain result when confidence is insufficient
            if best_prob < threshold:
                return MLPredictionResult(
                    status="abstain",
                    predicted_category=best_class,
                    confidence=best_prob,
                    probabilities=prob_dict,
                    model_name=self.metadata.get("model_name", "TypeMind_PatternClassifier"),
                    model_version=self.metadata.get("model_version", "1.0.0"),
                    features_used=active_features,
                    reason=(
                        f"Model confidence ({best_prob:.2f}) is below confidence threshold ({threshold:.2f}). "
                        f"Abstaining from diagnostic prediction."
                    ),
                )

            return MLPredictionResult(
                status="success",
                predicted_category=best_class,
                confidence=best_prob,
                probabilities=prob_dict,
                model_name=self.metadata.get("model_name", "TypeMind_PatternClassifier"),
                model_version=self.metadata.get("model_version", "1.0.0"),
                features_used=active_features,
            )

        except Exception as e:
            logger.error("Error during ML classification inference: %s", str(e), exc_info=True)
            return MLPredictionResult(
                status="uncertain",
                reason=f"Classification failed: {str(e)}",
            )
