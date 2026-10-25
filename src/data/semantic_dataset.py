"""Small admitted-log replay adapter. No generator, dataset exporter, or CLI.

The caller supplies a canonical successfully admitted prefix. Raw actions and
labels are deliberately outside this API. Gate C bulk preparation is not present.
"""
from dataclasses import dataclass

from src.features import extractor as shared
from src.features import FeatureEvent, FeatureHistory, FeatureRecord
from src.features.schema import FEATURE_NAMES, canonical_json, parse_json, identifier, integer
from .semantic_provenance import feature_metadata, validate_feature_metadata


@dataclass(frozen=True)
class FeatureRow:
    event_id: str
    namespace: str
    event_seq: int
    record: FeatureRecord

    def __post_init__(self):
        identifier(self.event_id, "event ID")
        identifier(self.namespace, "namespace")
        integer(self.event_seq, "event sequence")
        if type(self.record) is not FeatureRecord:
            raise ValueError("Invalid feature record")

    @property
    def vector(self):
        return shared.encode_vector(self.record)


def replay_events(events, namespace, *, snapshot=None):
    history = (FeatureHistory(namespace) if snapshot is None
               else FeatureHistory.from_snapshot(snapshot, namespace))
    rows = []
    for event in events:
        if type(event) is not FeatureEvent:
            raise ValueError("Replay accepts canonical admitted FeatureEvents only")
        record = shared.extract_features(event, history.view_before(event))
        shared.encode_vector(record)  # same encoding boundary as online
        history.commit_observation(event)
        rows.append(FeatureRow(event.event_id, namespace, event.event_seq, record))
    return tuple(rows)


def encode_rows(rows):
    """In-memory fixture codec, not a bulk preparation/file-writing operation."""
    return canonical_json({"metadata": feature_metadata(), "rows": [
        dict(event_id=row.event_id, namespace=row.namespace, event_seq=row.event_seq,
             values=[getattr(row.record, key) for key in FEATURE_NAMES])
        for row in rows
    ]})


def decode_rows(serialized):
    payload = parse_json(serialized)
    if (type(payload) is not dict or set(payload) != {"metadata", "rows"}
            or type(payload["rows"]) is not list):
        raise ValueError("Expected a versioned feature-row envelope")
    validate_feature_metadata(payload["metadata"])
    result, seen, last_seq = [], set(), {}
    for row in payload["rows"]:
        if (type(row) is not dict or set(row) != {"event_id", "namespace", "event_seq", "values"}
                or type(row["values"]) is not list or len(row["values"]) != 4):
            raise ValueError("Malformed feature row")
        identifier(row["event_id"], "event ID")
        identifier(row["namespace"], "namespace")
        integer(row["event_seq"], "event sequence")
        key = row["namespace"], row["event_id"]
        if key in seen:
            raise ValueError("Duplicate serialized event")
        if row["event_seq"] <= last_seq.get(row["namespace"], -1):
            raise ValueError("Backwards serialized sequence")
        last_seq[row["namespace"]] = row["event_seq"]
        seen.add(key)
        record = FeatureRecord(*row["values"])
        shared.encode_vector(record)
        result.append(FeatureRow(row["event_id"], row["namespace"], row["event_seq"], record))
    return tuple(result)
