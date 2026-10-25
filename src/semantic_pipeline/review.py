"""Approval-gated readiness/repeatability review, not research evaluation."""
import copy

from src.features import FeatureEvent
from src.features.schema import digest
from src.semantic_pipeline.authorization import require_permission, safe_name
from .storage import ImmutableArtifact, sha256_file
from .workflow import (paths, verified, _read, run_metadata, tracked_preservation, load_split)


def verify_preservation(config, *, execution_id, root, permit=None):
    require_permission(permit, config, execution_id, "verify-preservation")
    p = paths(root, execution_id)
    verified(p["evidence"] / "preflight", config, "preflight")
    expected = _read(p["evidence"] / "preflight/preservation.json")
    actual = tracked_preservation(p["root"])
    if expected != actual:
        raise ValueError("Protected files or branch references changed")
    with ImmutableArtifact(p["evidence"] / "preservation") as writer:
        writer.json("verification.json", dict(matches=True, protected_files=len(expected["files"]),
                                              branches=expected["branch_refs"]))
        return writer.finish(run_metadata(config, execution_id, p["root"], "preservation", permit=permit))


def validate_readiness(config, *, execution_id, root, detector, permit=None):
    require_permission(permit, config, execution_id, "validate-readiness")
    from src.data.semantic_collection import GateCEnvironment, setup_collection_environment, admit_candidate
    from src.data.semantic_generator import Candidate
    from src.detectors.semantic_train import load_model
    from src.detectors.semantic_policy import thresholds
    from src.environment.thresholds import ThresholdConfig
    p = paths(root, execution_id)
    _, _, rows = load_split(config, execution_id=execution_id, root=root, split="train",
                           operation="validate-readiness", permit=permit)
    adapter = load_model(p["models"] / detector, permit=permit, config=config, execution_id=execution_id,
                         operation="validate-readiness")
    verified(p["models"] / "policies" / detector, config, "decision_policy")
    record = _read(p["models"] / "policies" / detector / "policy.json")
    payload = dict(record)
    policy_id = payload.pop("policy_id")
    if (digest(payload) != policy_id or record["model_id"] != adapter.model_id
            or record["model_manifest"] != sha256_file(p["models"] / detector / "artifact_manifest.json")
            or record["dataset_manifest"] != sha256_file(p["dataset"] / "artifact_manifest.json")):
        raise ValueError("Decision-policy lineage mismatch")
    thresholds(record["flag_threshold"], record["block_threshold"])
    policy = ThresholdConfig(record["flag_threshold"], record["block_threshold"])
    # Every anchor is a clone of its collection prefix. Do not pretend a learned
    # BLOCK trajectory has the same later balances as the all-ALLOW collection.
    chosen = {r["event_id"]: r for r in rows[:16]}
    data = _read(p["collection"] / "entities.json")
    components = {c["component_id"]: c for c in data["components"]}
    environments, checks = {}, []
    with open(p["collection"] / "journal.jsonl", encoding="utf-8") as handle:
        from src.features.schema import parse_json
        for line in handle:
            entry = parse_json(line)
            candidate = Candidate(**entry["candidate"])
            component = components[candidate.component_id]
            if component["split"] != "train":
                continue
            env = environments.get(candidate.component_id)
            if env is None:
                env = environments[candidate.component_id] = setup_collection_environment(
                    component, data["entities"])
            if candidate.candidate_id in chosen:
                clone = GateCEnvironment(env.namespace, adapter, purpose="readiness",
                                         threshold_config=policy)
                clone._state = copy.deepcopy(env._state)
                clone.initial_snapshot = env.initial_snapshot
                result = clone.process_event(FeatureEvent(**entry["event"]))
                vector = chosen[candidate.candidate_id]["values"]
                if ([result["features"][k] for k in ("amount", "hour_of_day", "velocity_1h", "is_new_vpa")]
                        != vector):
                    raise ValueError("Model-readiness online/offline vector mismatch")
                checks.append(dict(event_id=candidate.candidate_id, decision=result["decision"],
                                   score=result["risk_score"], vector_equal=True))
            actual = admit_candidate(env, candidate)
            if actual != entry:
                raise ValueError("Changed collection prefix")
    if len(checks) != len(chosen) or not checks:
        raise ValueError("Missing readiness anchors")
    with ImmutableArtifact(p["evidence"] / ("readiness_" + detector)) as writer:
        writer.json("checks.json", dict(anchors=checks, scope="conditional_one_step_training_prefix",
                                        test_scored=False, research_validity_established=False))
        return writer.finish(run_metadata(config, execution_id, p["root"], "readiness", permit=permit,
                                         model_id=adapter.model_id, policy_id=policy_id))


def compare_repeats(config, *, execution_id, root, other_execution_id, permit=None):
    require_permission(permit, config, execution_id, "compare-repeats")
    require_permission(permit, config, other_execution_id, "compare-repeats")
    if execution_id == other_execution_id:
        raise ValueError("Independent execution IDs required")
    a, b = paths(root, execution_id), paths(root, other_execution_id)
    checks = {}
    for kind in ("collection", "dataset"):
        left, right = (verified(p[kind], config, kind) for p in (a, b))
        # Exclude run config-independent envelope; compare every semantic payload.
        if left["files"] != right["files"]:
            raise ValueError("Repeated collection/dataset payload differs")
        checks[kind] = left["files"]
    for detector in config.data["models"]:
        left, right = (verified(p["models"] / detector, config, "probability_model") for p in (a, b))
        semantic = ("configuration.json", "training_ids.json", "train_probabilities.f64")
        if any(left["files"][k] != right["files"][k] for k in semantic):
            raise ValueError("Repeated model configuration/predictions differ")
        checks[detector] = dict(
            model_bytes_equal=left["metadata"]["model_sha256"] == right["metadata"]["model_sha256"],
            predictions_equal=True)
        if not checks[detector]["model_bytes_equal"]:
            raise ValueError("Repeated probability-model bytes differ")
        lp, rp = (_read(p["models"] / "policies" / detector / "policy.json") for p in (a, b))
        for key in ("flag_threshold", "block_threshold", "counts", "supports", "validation_ids_sha256"):
            if lp[key] != rp[key]:
                raise ValueError("Repeated calibrated policy differs")
        checks[detector]["policy_equal"] = True
    with ImmutableArtifact(a["evidence"] / ("repeat_" + safe_name(other_execution_id))) as writer:
        writer.json("checks.json", checks)
        return writer.finish(run_metadata(config, execution_id, a["root"], "repeat_check", permit=permit,
                                         other_execution_id=other_execution_id))


def close_review(config, *, execution_id, root, other_execution_id, permit=None):
    require_permission(permit, config, execution_id, "close-review")
    p = paths(root, execution_id)
    required = dict(preflight="preflight", dataset_validation="dataset_validation", preservation="preservation",
                    **{f"model_validation_{d}": "model_validation" for d in config.data["models"]},
                    **{f"readiness_{d}": "readiness" for d in config.data["models"]},
                    **{"repeat_" + safe_name(other_execution_id): "repeat_check"})
    references = {}
    for directory, kind in required.items():
        verified(p["evidence"] / directory, config, kind)
        references[directory] = sha256_file(p["evidence"] / directory / "artifact_manifest.json")
    # Recheck protection now, without overwriting the previous preservation proof.
    if tracked_preservation(p["root"]) != _read(p["evidence"] / "preflight/preservation.json"):
        raise ValueError("Preservation changed after verification")
    with ImmutableArtifact(p["evidence"] / "closure") as writer:
        writer.json("review.json", dict(evidence=references, gate_d_authorized=False,
                                        final_test_scored=False, human_acceptance_required=True,
                                        legacy_models_compatible=False))
        return writer.finish(run_metadata(config, execution_id, p["root"], "closure_candidate", permit=permit))
