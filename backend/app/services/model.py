"""Machine Learning model metadata service."""

import logging
from typing import Optional
from app.ml.predictor import TypePatternPredictor
from app.schemas.ml import ModelInfoResponse

logger = logging.getLogger("typemind.services.model")


class ModelService:
    """Service providing metadata, architecture, features, and evaluation metrics for the ML model."""

    def __init__(self, predictor: Optional[TypePatternPredictor] = None) -> None:
        self.predictor = predictor or TypePatternPredictor()

    def get_model_info(self) -> ModelInfoResponse:
        """Return structured model metadata. Gracefully degrades if model is unavailable."""
        try:
            if not self.predictor.is_available:
                logger.info("ML model is currently unavailable or uninitialized.")
                return ModelInfoResponse(
                    status="unavailable",
                    model_name=None,
                    model_version=None,
                    model_architecture=None,
                    trained_at=None,
                    features_count=0,
                    classes=[],
                    evaluation_summary=None,
                    dataset_info=None,
                )

            metadata = self.predictor.metadata or {}
            features_meta = metadata.get("features", {})
            features_count = features_meta.get("count", len(features_meta.get("names", [])))

            evaluation = metadata.get("evaluation", {})
            evaluation_summary = evaluation.get("chosen_model") or evaluation

            return ModelInfoResponse(
                status="loaded",
                model_name=metadata.get("model_name", "TypeMind_PatternClassifier"),
                model_version=metadata.get("model_version", "1.0.0"),
                model_architecture=metadata.get("model_architecture", "RandomForestClassifier"),
                trained_at=metadata.get("trained_at"),
                features_count=features_count,
                classes=metadata.get("classes", []),
                evaluation_summary=evaluation_summary,
                dataset_info=metadata.get("dataset_info"),
            )

        except Exception as exc:
            logger.error("Failed to retrieve model info: %s", str(exc), exc_info=True)
            return ModelInfoResponse(
                status="unavailable",
                model_name=None,
                model_version=None,
                model_architecture=None,
                trained_at=None,
                features_count=0,
                classes=[],
                evaluation_summary=None,
                dataset_info=None,
            )


_model_service = ModelService()


def get_model_service() -> ModelService:
    """Dependency provider returning singleton ModelService."""
    return _model_service
