"""Independent structural, chronological and label-link checks."""
import math

from src.data.semantic_provenance import validate_feature_metadata
from src.features import FeatureEvent, FeatureHistory, timestamp_us
from src.features.extractor import FeatureRecord, encode_vector
from src.features.schema import identifier, integer
from .config import SPLITS


def authorize_split(operation, split):
    allowed = {"train": {"train"}, "calibrate": {"validation"},
               "validate-model": {"train"}, "validate-readiness": {"train"}}
    if operation not in allowed or split not in allowed[operation]:
        raise PermissionError("Final-test model access and unapproved split access are forbidden")


def authorize_profile(profile, operation):
    if profile != "baseline":
        raise PermissionError("Pilot artifacts are for integrity inspection, never model/policy inputs")
    if operation not in ("train", "calibrate", "validate-model", "validate-readiness"):
        raise PermissionError("Unsupported model operation")


def validate_collection_counts(component_ids, records, declared, candidate_cap):
    """Independent terminal/budget check; catches sealed but truncated journals."""
    if len(set(component_ids)) != len(component_ids) or set(declared) != set(component_ids):
        raise ValueError("Missing/duplicate component accounting")
    grouped, ids = {key: [] for key in component_ids}, set()
    for record in records:
        c = record["candidate"]
        if c["component_id"] not in grouped or c["candidate_id"] in ids:
            raise ValueError("Unknown component or reused candidate ID")
        ids.add(c["candidate_id"])
        grouped[c["component_id"]].append(record)
    for key, rows in grouped.items():
        if not rows or len(rows) > candidate_cap:
            raise ValueError("Missing or over-budget candidates")
        if [r["candidate"]["candidate_seq"] for r in rows] != list(range(len(rows))):
            raise ValueError("Candidate sequence gap")
        if any(r["candidate"]["horizon_exceeded"] for r in rows[:-1]):
            raise ValueError("Candidate after terminal horizon")
        horizon = rows[-1]["candidate"]["horizon_exceeded"]
        if not horizon and len(rows) != candidate_cap:
            raise ValueError("Truncated journal without valid termination")
        if any(r["kind"] not in ("admitted", "rejected") for r in rows):
            raise ValueError("Unknown admission status")
        expected = dict(candidates=len(rows),
                        admitted=sum(r["kind"] == "admitted" for r in rows),
                        rejected=sum(r["kind"] == "rejected" for r in rows),
                        termination="episode_horizon" if horizon else "candidate_cap")
        if declared[key] != expected or (horizon and rows[-1]["kind"] != "rejected"):
            raise ValueError("Component counts or terminal rejection mismatch")


def validate_partition_graph(entities, events, config):
    owners, accounts, components, namespaces, vpas = {}, {}, {}, {}, {}
    for row in entities:
        group = tuple(identifier(row[key], key) for key in ("component_id", "namespace", "split"))
        component, namespace, split = group
        if split not in SPLITS:
            raise ValueError("Unknown split")
        if components.setdefault(component, (namespace, split)) != (namespace, split):
            raise ValueError("Component spans namespaces/splits")
        if namespaces.setdefault(namespace, (component, split)) != (component, split):
            raise ValueError("Namespace bridges components/splits")
        account = identifier(row["account_id"], "account")
        vpa = identifier(row["vpa_id"], "VPA", vpa=True)
        if accounts.setdefault(account, group) != group or vpa in vpas:
            raise ValueError("Account overlap or duplicate alias")
        if "initial_balance_paise" in row:
            integer(row["initial_balance_paise"], "initial balance", 0, 10**12)
            integer(row["created_time_us"], "creation time")
            if (row["created_time_us"] > timestamp_us(config.data["splits"][split][0])
                    or type(row["merchant"]) is not bool):
                raise ValueError("Future account creation or invalid entity role")
            state = (row["initial_balance_paise"], row["created_time_us"], row["merchant"])
            if owners.setdefault(account, state) != state:
                raise ValueError("Inconsistent alias account state")
        vpas[vpa] = (account, group)
    histories, ids = {}, set()
    for raw in events:
        event = FeatureEvent(**raw)
        if event.event_id in ids:
            raise ValueError("Duplicate event ID")
        ids.add(event.event_id)
        source, target = vpas.get(event.source_vpa_id), vpas.get(event.beneficiary_vpa_id)
        if (source is None or target is None or source[0] == target[0]
                or source[1] != target[1] or event.history_namespace != source[1][1]):
            raise ValueError("Unknown entity, alias transfer, or component bridge")
        start, end = map(timestamp_us, config.data["splits"][source[1][2]])
        if not start <= event.event_time_utc_us < end:
            raise ValueError("Event violates its split temporal window")
        history = histories.setdefault(event.history_namespace, FeatureHistory(event.history_namespace))
        if event.event_seq != history.next_sequence:
            raise ValueError("Noncontiguous event sequence")
        history.commit_observation(event)
    return {"entities": len(entities), "accounts": len(accounts),
            "components": len(components), "events": len(ids)}


def validate_table_links(rows, labels, event_ids, metadata):
    validate_feature_metadata(metadata)
    if len(event_ids) != len(set(event_ids)):
        raise ValueError("Duplicate event membership")
    expected, seen_rows, seen_labels = set(event_ids), set(), set()
    for row in rows:
        if set(row) != {"event_id", "namespace", "event_seq", "values"}:
            raise ValueError("Extra/leaking or missing feature-row fields")
        identifier(row["namespace"], "namespace")
        integer(row["event_seq"], "event sequence")
        key = identifier(row["event_id"], "event ID")
        if key not in expected or key in seen_rows:
            raise ValueError("Feature row membership mismatch")
        seen_rows.add(key)
        values = row["values"]
        if (type(values) is not list or len(values) != 4
                or any(type(v) not in (int, float) for v in values)
                or any(not math.isfinite(v) for v in values)
                or any(int(v) != v for v in values[1:])):
            raise ValueError("Invalid encoded feature domains")
        encode_vector(FeatureRecord(float(values[0]), *(int(v) for v in values[1:])))
    for label in labels:
        if set(label) != {"event_id", "target"}:
            raise ValueError("Labels must remain a separate two-field table")
        key = identifier(label["event_id"], "label event ID")
        integer(label["target"], "target", 0, 1)
        if key not in expected or key in seen_labels:
            raise ValueError("Label membership mismatch")
        seen_labels.add(key)
    if seen_rows != expected or seen_labels != expected:
        raise ValueError("Feature/label membership is not one-to-one and exhaustive")
    return {"rows": len(expected), "label_integrity": True}
