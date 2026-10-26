"""Machine learning package.

Exports feature extraction, training pipelines, and prediction services.
"""

from app.ml.features import CodePatternFeatureExtractor
from app.ml.predictor import MLPredictionResult, TypePatternPredictor
from app.ml.train import train_and_evaluate

__all__ = [
    "CodePatternFeatureExtractor",
    "TypePatternPredictor",
    "MLPredictionResult",
    "train_and_evaluate",
]
