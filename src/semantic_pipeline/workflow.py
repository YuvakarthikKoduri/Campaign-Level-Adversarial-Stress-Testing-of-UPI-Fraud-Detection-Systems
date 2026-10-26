"""Approval-gated batch workflows. Importing this module runs no workflow."""
from importlib import metadata as packages
from pathlib import Path
import platform
import subprocess

import numpy as np

from src.data.semantic_provenance import feature_metadata, validate_feature_metadata
from src.features import FeatureEvent, FeatureHistory
from src.features import extractor as shared
from src.features.schema import canonical_json, digest, parse_json
from .authorization import require_permission, safe_name
from .config import SPLITS
from .integrity import validate_partition_graph, validate_table_links, authorize_split, authorize_profile
from .integrity import validate_collection_counts
from .storage import ImmutableArtifact, verify_artifact, sha256_file

DEPENDENCIES = ("numpy", "pandas", "scikit-learn", "scipy", "joblib", "xgboost",
                "threadpoolctl", "pytest")


def environment_record():
    return {"python": platform.python_version(), "platform": platform.platform(),
            "packages": {name: packages.version(name) for name in DEPENDENCIES}}


def paths(root, execution_id):
    root = Path(root).resolve()
    safe_name(execution_id)
    return dict(root=root,
                collection=root / "data/semantic_v2" / execution_id / "collection",
                dataset=root / "data/semantic_v2" / execution_id / "dataset",
                models=root / "models/semantic_v2" / execution_id,
                evidence=root / "results/semantic_v2/gate_c" / execution_id)


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def tracked_preservation(root):
    names = subprocess.check_output(["git", "-C", str(root), "ls-files", "-z"]).decode().split("\0")
    hashes = {}
    for name in filter(None, names):
        path = Path(root) / name
        if path.is_symlink() or not path.is_file():
            raise ValueError("Missing or symlinked protected tracked file")
        hashes[name] = sha256_file(path)
    refs = {}
    for name in ("master", "main", "repair/milestone-1-correctness-reproducibility",
                 "feature/gate-b-semantic-parity"):
        result = subprocess.run(["git", "-C", str(root), "rev-parse", "--verify", "refs/heads/" + name],
                                capture_output=True, text=True)
        if result.returncode == 0:
            refs[name] = result.stdout.strip()
    return dict(files=hashes, branch_refs=refs)


def _read(path):
    return parse_json(Path(path).read_text(encoding="utf-8"))


def verified(path, config, kind):
    manifest = verify_artifact(path)
    meta = manifest["metadata"]
    if meta.get("kind") != kind or meta.get("config_digest") != config.digest:
        raise ValueError("Artifact/config identity mismatch")
    validate_feature_metadata(meta["feature_metadata"])
    return manifest


def run_metadata(config, execution_id, root, kind, *, permit, **extra):
    return dict(kind=kind, config_digest=config.digest, generation_digest=config.generation_digest,
                execution_id=execution_id, feature_metadata=feature_metadata(),
                implementation_commit=git(root, "rev-parse", "HEAD"),
                approval_reference=permit.approval_reference,
                environment=environment_record(), **extra)


def preflight(config, *, execution_id, root, permit=None, profile="baseline"):
    require_permission(permit, config, execution_id, "preflight")
    p = paths(root, execution_id)
    subprocess.run(["git", "-C", str(p["root"]), "merge-base", "--is-ancestor",
                    config.data["base_commit"], "HEAD"], check=True)
    if git(p["root"], "diff", "HEAD", "--"):
        raise ValueError("Commit reviewed source before execution")
    if profile not in config.data["profiles"]:
        raise ValueError("Unknown profile")
    for name in ("collection", "dataset", "models"):
        if p[name].exists() or p[name].is_symlink():
            raise FileExistsError(p[name])
    with ImmutableArtifact(p["evidence"] / "preflight") as writer:
        writer.json("preservation.json", tracked_preservation(p["root"]))
        writer.json("config.json", config.data)
        return writer.finish(run_metadata(config, execution_id, p["root"], "preflight",
                                          permit=permit, profile=profile))


def collect(config, *, execution_id, root, permit=None, profile="baseline"):
    require_permission(permit, config, execution_id, "collect")
    from src.data.semantic_entities import generate_entities, derive_seed
    from src.data.semantic_generator import generate_candidates
    from src.data.semantic_collection import setup_collection_environment, admit_candidate
    p = paths(root, execution_id)
    pre = verified(p["evidence"] / "preflight", config, "preflight")
    if pre["metadata"]["profile"] != profile:
        raise ValueError("Profile differs from approved preflight")
    entity_data = generate_entities(config, execution_id=execution_id, permit=permit, profile=profile)
    components = {c["component_id"]: c for c in entity_data["components"]}
    counts, env, active = {}, None, None
    with ImmutableArtifact(p["collection"]) as writer:
        writer.json("entities.json", entity_data)
        journal_path = writer.stage / "journal.jsonl"
        with open(journal_path, "xb") as journal:
            def append(record):
                line = (canonical_json(record) + "\n").encode()
                if journal.write(line) != len(line):
                    raise OSError("Partial candidate journal write")
                journal.flush()
            for candidate in generate_candidates(config, execution_id=execution_id, permit=permit,
                                                 profile=profile, entity_data=entity_data):
                if candidate.component_id != active:
                    active = candidate.component_id
                    env = setup_collection_environment(components[active], entity_data["entities"])
                    counts[active] = {"admitted": 0, "rejected": 0, "candidates": 0,
                                     "termination": "candidate_cap"}
                record = admit_candidate(env, candidate, journal_append=append)
                counts[active][record["kind"]] += 1
                counts[active]["candidates"] += 1
                if candidate.horizon_exceeded:
                    counts[active]["termination"] = "episode_horizon"
            import os
            os.fsync(journal.fileno())
        writer.json("component_counts.json", counts)
        # Per-candidate roles are fully reconstructible, independent of rejection.
        writer.json("seed_contract.json", dict(
            root=config.data["root_seed"], algorithm=config.data["seed_derivation"],
            candidate_roles=["behavior", "timing"], candidate_keys=["component_id", "candidate_seq"],
            label_role="intent", split_seed=entity_data["split_seed"],
            example_model_seed=derive_seed(config.data["root_seed"], "model", "xgboost", bits=32)))
        writer.json("config.json", config.data)
        return writer.finish(run_metadata(config, execution_id, p["root"], "collection",
                                         permit=permit, profile=profile,
                                         preflight_manifest=sha256_file(
                                             p["evidence"] / "preflight/artifact_manifest.json")))


def replay_journal(entity_data, records, config):
    """Deterministic literal-record replay; never creates candidates or fits models."""
    from src.data.semantic_collection import setup_collection_environment, admit_candidate
    from src.data.semantic_generator import Candidate
    components = {c["component_id"]: c for c in entity_data["components"]}
    if len(components) != len(entity_data["components"]):
        raise ValueError("Duplicate component")
    environments, sequences, admitted, exclusions = {}, {}, [], []
    closed, active = set(), None
    for record in records:
        candidate = Candidate(**record["candidate"])
        key = candidate.component_id
        if key not in components or candidate.history_namespace != components[key]["namespace"]:
            raise ValueError("Candidate namespace/component mismatch")
        if key in closed:
            raise ValueError("Interleaved/closed component")
        if active != key:
            if active is not None:
                closed.add(active)
            active = key
        if candidate.candidate_seq != sequences.get(key, 0):
            raise ValueError("Missing/duplicate candidate sequence")
        component = components[key]
        intent = int(component["mixed"] and component["attack_start"] <= candidate.candidate_seq
                     < component["attack_start"] + component["attack_length"])
        if (candidate.intent != intent
                or candidate.family != (component["family"] if intent else "benign")
                or candidate.horizon_exceeded != (
                    candidate.event_time_utc_us > component["start_time_us"]
                    + config.data["behavior"]["episode_seconds"] * 1_000_000)):
            raise ValueError("Latent label schedule or horizon disagrees with component metadata")
        sequences[key] = candidate.candidate_seq + 1
        env = environments.setdefault(key, None)
        if env is None:
            env = environments[key] = setup_collection_environment(components[key], entity_data["entities"])
        expected = admit_candidate(env, candidate)
        if canonical_json(expected) != canonical_json(record):
            raise ValueError("Journal is inconsistent with deterministic ledger/admission replay")
        if expected["kind"] == "admitted":
            admitted.append(expected)
        else:
            exclusions.append(dict(candidate_id=candidate.candidate_id,
                                   reason=expected["outcome"]["details"]))
    return admitted, exclusions


def prepare(config, *, execution_id, root, permit=None):
    require_permission(permit, config, execution_id, "prepare")
    p = paths(root, execution_id)
    collection_manifest = verified(p["collection"], config, "collection")
    data = _read(p["collection"] / "entities.json")
    with open(p["collection"] / "journal.jsonl", encoding="utf-8") as handle:
        records = [parse_json(line) for line in handle]
    validate_collection_counts(
        [c["component_id"] for c in data["components"]], records,
        _read(p["collection"] / "component_counts.json"),
        config.data["profiles"][collection_manifest["metadata"]["profile"]]["candidate_cap"])
    admitted, exclusions = replay_journal(data, records, config)
    events = [r["event"] for r in admitted]
    validate_partition_graph(data["entities"], events, config)
    component_split = {r["namespace"]: r["split"] for r in data["entities"]}
    histories, rows, labels = {}, {s: [] for s in SPLITS}, {s: [] for s in SPLITS}
    membership = {}
    for entry in admitted:
        event = FeatureEvent(**entry["event"])
        history = histories.setdefault(event.history_namespace, FeatureHistory(event.history_namespace))
        vector = shared.encode_vector(shared.extract_features(event, history.view_before(event)))[0].tolist()
        if vector != entry["features"]:
            raise ValueError("Offline/online vector mismatch")
        history.commit_observation(event)
        split = component_split[event.history_namespace]
        row = dict(event_id=event.event_id, namespace=event.history_namespace,
                   event_seq=event.event_seq, values=vector)
        rows[split].append(row)
        labels[split].append(dict(event_id=event.event_id, target=entry["label"]["target"]))
        membership[event.event_id] = split
    with ImmutableArtifact(p["dataset"]) as writer:
        for split in SPLITS:
            ids = [r["event_id"] for r in rows[split]]
            if not ids:
                raise ValueError("Empty split; no silent resampling")
            validate_table_links(rows[split], labels[split], ids, feature_metadata())
            writer.json(f"{split}/features.json", rows[split])
            writer.json(f"{split}/labels.json", labels[split])
            writer.json(f"{split}/event_ids.json", ids)
        writer.json("entities.json", data)
        writer.json("events.json", events)
        writer.json("membership.json", membership)
        writer.json("exclusions.json", exclusions)
        writer.json("test_seal.json", dict(sealed=True, model_scoring_authorized=False,
                                           event_ids_sha256=digest([r["event_id"] for r in rows["test"]])))
        writer.json("config.json", config.data)
        return writer.finish(run_metadata(config, execution_id, p["root"], "dataset", permit=permit,
                    profile=collection_manifest["metadata"]["profile"],
                    collection_manifest=sha256_file(p["collection"] / "artifact_manifest.json")))


def _validate_dataset(config, execution_id, root):
    p = paths(root, execution_id)
    manifest = verified(p["dataset"], config, "dataset")
    collection = verified(p["collection"], config, "collection")
    if manifest["metadata"]["profile"] != collection["metadata"]["profile"]:
        raise ValueError("Dataset/collection profile mismatch")
    if manifest["metadata"]["collection_manifest"] != sha256_file(p["collection"] / "artifact_manifest.json"):
        raise ValueError("Collection lineage mismatch")
    data, events = _read(p["dataset"] / "entities.json"), _read(p["dataset"] / "events.json")
    if data != _read(p["collection"] / "entities.json"):
        raise ValueError("Entity lineage mismatch")
    with open(p["collection"] / "journal.jsonl", encoding="utf-8") as handle:
        records = [parse_json(line) for line in handle]
    validate_collection_counts(
        [c["component_id"] for c in data["components"]], records,
        _read(p["collection"] / "component_counts.json"),
        config.data["profiles"][collection["metadata"]["profile"]]["candidate_cap"])
    admitted, exclusions = replay_journal(data, records, config)
    if (events != [r["event"] for r in admitted]
            or exclusions != _read(p["dataset"] / "exclusions.json")):
        raise ValueError("Admission/exclusion lineage mismatch")
    targets = {r["event"]["event_id"]: r["label"]["target"] for r in admitted}
    result = validate_partition_graph(data["entities"], events, config)
    membership, event_map = _read(p["dataset"] / "membership.json"), {e["event_id"]: e for e in events}
    if set(membership) != set(event_map):
        raise ValueError("Nonexhaustive membership")
    seen = set()
    entity_splits = {r["namespace"]: r["split"] for r in data["entities"]}
    histories, expected = {}, {}
    for raw in events:
        event = FeatureEvent(**raw)
        history = histories.setdefault(event.history_namespace, FeatureHistory(event.history_namespace))
        expected[event.event_id] = shared.encode_vector(
            shared.extract_features(event, history.view_before(event)))[0].tolist()
        history.commit_observation(event)
    for split in SPLITS:
        ids = _read(p["dataset"] / split / "event_ids.json")
        rows, labels = (_read(p["dataset"] / split / f"{name}.json") for name in ("features", "labels"))
        validate_table_links(rows, labels, ids, feature_metadata())
        if any(label["target"] != targets.get(label["event_id"]) for label in labels):
            raise ValueError("Label disagrees with latent intent schedule")
        if not ids or seen & set(ids):
            raise ValueError("Empty/overlapping split")
        seen.update(ids)
        for row in rows:
            event = event_map[row["event_id"]]
            if (membership[row["event_id"]] != split or entity_splits[row["namespace"]] != split
                    or row["namespace"] != event["history_namespace"]
                    or row["event_seq"] != event["event_seq"]
                    or row["values"] != expected[row["event_id"]]):
                raise ValueError("Split membership or causal feature mismatch")
    if seen != set(event_map):
        raise ValueError("Omitted split rows")
    seal = _read(p["dataset"] / "test_seal.json")
    if seal != dict(sealed=True, model_scoring_authorized=False,
                    event_ids_sha256=digest(_read(p["dataset"] / "test/event_ids.json"))):
        raise ValueError("Corrupt final-test seal")
    return result


def validate_dataset(config, *, execution_id, root, permit=None):
    require_permission(permit, config, execution_id, "validate-dataset")
    result = _validate_dataset(config, execution_id, root)
    p = paths(root, execution_id)
    with ImmutableArtifact(p["evidence"] / "dataset_validation") as writer:
        writer.json("checks.json", result)
        return writer.finish(run_metadata(config, execution_id, p["root"], "dataset_validation", permit=permit,
                                         dataset_manifest=sha256_file(p["dataset"] / "artifact_manifest.json")))


def load_split(config, *, execution_id, root, split, operation, permit):
    require_permission(permit, config, execution_id, operation)
    authorize_split(operation, split)
    p = paths(root, execution_id)
    dataset = verified(p["dataset"], config, "dataset")
    authorize_profile(dataset["metadata"]["profile"], operation)
    validation = verified(p["evidence"] / "dataset_validation", config, "dataset_validation")
    if validation["metadata"]["dataset_manifest"] != sha256_file(p["dataset"] / "artifact_manifest.json"):
        raise ValueError("Dataset not structurally validated")
    ids = _read(p["dataset"] / split / "event_ids.json")
    rows = _read(p["dataset"] / split / "features.json")
    labels = _read(p["dataset"] / split / "labels.json")
    validate_table_links(rows, labels, ids, feature_metadata())
    label_map = {r["event_id"]: r["target"] for r in labels}
    return (np.asarray([r["values"] for r in rows], dtype=np.float64),
            np.asarray([label_map[r["event_id"]] for r in rows], dtype=np.int64), rows)
