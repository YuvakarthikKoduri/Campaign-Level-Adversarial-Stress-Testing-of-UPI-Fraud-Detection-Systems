"""Opt-in semantic probability adapter; policy is deliberately not part of identity."""
import numpy as np

from src.data.semantic_provenance import validate_feature_metadata


class SemanticModelDetector:
    fixture_only = False

    def __init__(self, estimator, metadata, model_id):
        validate_feature_metadata(metadata)
        self.estimator, self.metadata, self.model_id = estimator, dict(metadata), model_id

    def predict(self, vector):
        from .semantic_train import validate_probability_matrix
        validate_feature_metadata(self.metadata)
        if (not isinstance(vector, np.ndarray) or vector.dtype != np.float64
                or vector.shape != (1, 4) or not np.isfinite(vector).all()):
            raise ValueError("Shared float64 (1,4) vector required")
        return float(validate_probability_matrix(
            self.estimator.predict_proba(vector), self.estimator.classes_)[0])
