"""Gate B fixture-only vector adapter; intentionally no trained-artifact loader."""
import math

import numpy as np

from src.data.semantic_provenance import feature_metadata, validate_feature_metadata


class FixtureDetector:
    """Explicit deterministic test double, never an authoritative research model."""
    fixture_only = True

    def __init__(self, predict_vector, *, metadata=None):
        if not callable(predict_vector):
            raise ValueError("A fixture vector predictor is required")
        self.predict_vector = predict_vector
        self.metadata = feature_metadata() if metadata is None else dict(metadata)
        validate_feature_metadata(self.metadata)

    def predict(self, vector):
        validate_feature_metadata(self.metadata)
        if (not isinstance(vector, np.ndarray) or vector.dtype != np.float64
                or vector.shape != (1, 4) or not np.isfinite(vector).all()):
            raise ValueError("Semantic detector requires the shared float64 vector")
        result = self.predict_vector(vector)
        if isinstance(result, (bool, np.bool_)) or not isinstance(result, (int, float, np.number)):
            raise ValueError("Invalid predictor probability type")
        result = float(result)
        if not math.isfinite(result) or not 0 <= result <= 1:
            raise ValueError("Invalid predictor probability")
        return result
