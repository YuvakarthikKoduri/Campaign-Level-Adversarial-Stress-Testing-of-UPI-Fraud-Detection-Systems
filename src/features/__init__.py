"""Public semantic-v2 feature API. Legacy paths remain opt-in and unchanged."""
from .events import FeatureEvent, timestamp_us
from .history import FeatureHistory, HistorySnapshot
from .schema import CONTRACT_ID, SCHEMA_DIGEST, FEATURE_NAMES
from .extractor import FeatureRecord, extract_features, encode_vector

__all__ = [
    "FeatureEvent", "timestamp_us", "FeatureHistory", "HistorySnapshot",
    "CONTRACT_ID", "SCHEMA_DIGEST", "FEATURE_NAMES",
    "FeatureRecord", "extract_features", "encode_vector",
]
