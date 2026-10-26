"""Read-only feature-contract and split validators. No dataset/model writers."""
import hashlib
from pathlib import Path

from src.features.schema import CONTRACT_ID, SCHEMA_DIGEST, identifier


def feature_metadata():
    # Hash every semantic implementation input, not merely column names.
    root = Path(__file__).resolve().parents[1] / "features"
    source = hashlib.sha256()
    for name in ("schema.py", "events.py", "history.py", "extractor.py"):
        source.update(name.encode("ascii") + b"\0" + (root / name).read_bytes() + b"\0")
    return {
        "contract_id": CONTRACT_ID,
        "schema_digest": SCHEMA_DIGEST,
        "extractor_source_digest": source.hexdigest(),
    }


def validate_feature_metadata(metadata):
    if type(metadata) is not dict or metadata != feature_metadata():
        raise ValueError("Feature contract/schema/extractor metadata mismatch")


def validate_splits(splits, event_groups):
    if (type(splits) is not dict or set(splits) != {"train", "validation", "test"}
            or type(event_groups) is not dict):
        raise ValueError("Explicit train/validation/test membership required")
    seen_ids, seen_groups = set(), set()
    for name in ("train", "validation", "test"):
        rows = splits[name]
        if (type(rows) is not list or not rows or any(type(row) is not str for row in rows)
                or len(set(rows)) != len(rows)):
            raise ValueError("Split membership must be explicit, nonempty, unique")
        groups = set()
        for event_id in rows:
            identifier(event_id, "split event ID")
            if event_id not in event_groups or event_id in seen_ids:
                raise ValueError("Missing/overlapping event membership")
            groups.add(identifier(event_groups[event_id], "entity group"))
        if groups & seen_groups:
            raise ValueError("Prohibited entity-group overlap")
        seen_ids.update(rows)
        seen_groups.update(groups)
    if seen_ids != set(event_groups):
        raise ValueError("Membership is not exhaustive for the declared row map")
