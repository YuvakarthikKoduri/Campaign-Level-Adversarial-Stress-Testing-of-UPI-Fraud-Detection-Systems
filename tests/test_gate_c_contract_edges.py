"""Independent literal oracles and negative boundaries; no workflow execution."""
import ast
import copy
import inspect

import numpy as np
import pytest

from src.data.semantic_collection import CollectionObserver, GateCEnvironment, admit_candidate
from src.data.semantic_dataset import replay_events
from src.data.semantic_generator import Candidate
from src.features import FeatureEvent
from src.semantic_pipeline.config import load_config, PipelineConfig
from src.semantic_pipeline.authorization import ExecutionDenied
from src.semantic_pipeline.storage import ImmutableArtifact, verify_artifact

T = 1767614400000000


def literal_env():
    env = GateCEnvironment("n", CollectionObserver(), purpose="collection")
    for who in ("a", "b"):
        env.create_account(who, 10000)
        env.create_vpa(who + "@upi", who, who)
    return env


def test_independent_window_novelty_and_parity_oracle():
    env = literal_env()
    # Exact one-hour boundary drops event 0; same-time prior event 1 counts.
    literals = [(T, "a@upi", "b@upi"), (T + 3_600_000_000, "a@upi", "b@upi"),
                (T + 3_600_000_000, "a@upi", "b@upi"),
                (T + 3_600_000_001, "b@upi", "a@upi")]
    events, actual = [], []
    for seq, (when, source, target) in enumerate(literals):
        c = Candidate(f"e{seq}", "g", "n", seq, when, source, target, 100, 0, "benign")
        record = admit_candidate(env, c)
        events.append(FeatureEvent(**record["event"]))
        actual.append(record["features"])
    expected = [[1., 12., 0., 1.], [1., 13., 0., 0.],
                [1., 13., 1., 0.], [1., 13., 0., 1.]]
    assert actual == expected
    assert [r.vector[0].tolist() for r in replay_events(events, "n")] == expected
    assert admit_candidate(literal_env(), Candidate(
        "fresh", "g", "n", 0, T, "a@upi", "b@upi", 100, 0, "benign"))["features"] == expected[0]


def test_score_failure_and_corrupt_ledger_do_not_commit(monkeypatch):
    env = literal_env()
    original = env._state
    def fail(self, vector):
        raise RuntimeError("injected inference failure")
    monkeypatch.setattr(CollectionObserver, "predict", fail)
    with pytest.raises(Exception):
        admit_candidate(env, Candidate("e", "g", "n", 0, T, "a@upi", "b@upi", 100, 0, "benign"))
    assert env.run_invalid and env._state is original and env.history.next_sequence == 0


@pytest.mark.parametrize("mutation", [
    lambda d: d["behavior"].update(velocity_1h=7),
    lambda d: d["behavior"].pop("routine_delay"),
    lambda d: d["policy"].pop("minimum_fraud_components"),
    lambda d: d["models"]["xgboost"].update(eval_set="test"),
    lambda d: d["profiles"]["pilot"].update(split_counts=[14, 5, 6]),
    lambda d: d["feature_metadata"].update(contract_id="different"),
])
def test_missing_or_leaking_configuration_rejected(mutation):
    data = load_config().data
    mutation(data)
    with pytest.raises((ValueError, KeyError)):
        PipelineConfig.from_dict(data)


@pytest.mark.parametrize("change", ["unlisted", "incomplete", "manifest", "symlink"])
def test_corrupt_literal_artifact_rejected(tmp_path, change):
    target = tmp_path / "literal"
    with ImmutableArtifact(target) as writer:
        writer.json("fixture.json", {"literal": True})
        writer.finish({"kind": "test"})
    if change == "unlisted":
        (target / "extra").write_text("extra")
    elif change == "incomplete":
        (target / "COMPLETE").unlink()
    elif change == "manifest":
        (target / "artifact_manifest.json").write_text('{"format":"unknown"}')
    else:
        (target / "fixture.json").unlink()
        (target / "fixture.json").symlink_to(tmp_path / "outside")
    with pytest.raises(ValueError):
        verify_artifact(target)


def test_every_production_entry_has_approval_as_first_statement():
    from src.semantic_pipeline import workflow, review
    from src.detectors import semantic_train, semantic_policy
    from src.data import semantic_entities, semantic_generator
    functions = [workflow.preflight, workflow.collect, workflow.prepare, workflow.validate_dataset,
                 semantic_train.train_model, semantic_train.load_model, semantic_train.validate_model,
                 semantic_policy.calibrate, review.validate_readiness, review.verify_preservation,
                 review.compare_repeats, review.close_review,
                 semantic_entities.generate_entities, semantic_generator.generate_candidates]
    for function in functions:
        tree = ast.parse(inspect.getsource(function))
        first = tree.body[0].body[0]
        assert isinstance(first, ast.Expr) and isinstance(first.value, ast.Call)
        assert first.value.func.id == "require_permission", function.__name__


def test_pilot_never_becomes_model_input():
    from src.semantic_pipeline.integrity import authorize_profile
    for operation in ("train", "calibrate", "validate-model", "validate-readiness"):
        with pytest.raises(PermissionError):
            authorize_profile("pilot", operation)
        authorize_profile("baseline", operation)


def test_publish_failure_revokes_staged_complete_marker(tmp_path, monkeypatch):
    import src.semantic_pipeline.storage as storage
    def fail(*args):
        raise OSError("injected publish failure")
    monkeypatch.setattr(storage.os, "rename", fail)
    target = tmp_path / "literal"
    with pytest.raises(OSError):
        with ImmutableArtifact(target) as writer:
            writer.json("fixture.json", {"literal": True})
            writer.finish({"kind": "literal"})
    assert not target.exists()
    stages = list(tmp_path.glob(".literal.incomplete-*"))
    assert len(stages) == 1 and not (stages[0] / "COMPLETE").exists()
    assert (stages[0] / "fixture.json").exists()


def test_effective_parameter_defaults_are_explicit_json_values():
    from src.detectors.semantic_train import parameter_record
    from src.features.schema import canonical_json
    value = parameter_record({"missing": float("nan"), "seed": np.int64(4)})
    assert value == {"missing": {"library_nonfinite": "nan"}, "seed": 4}
    assert "NaN" not in canonical_json(value)


def test_literal_journal_budget_and_truncation_checks():
    from src.semantic_pipeline.integrity import validate_collection_counts
    rows = [{"candidate": {"component_id": "g", "candidate_id": "c0", "candidate_seq": 0,
                           "horizon_exceeded": False}, "kind": "admitted"},
            {"candidate": {"component_id": "g", "candidate_id": "c1", "candidate_seq": 1,
                           "horizon_exceeded": True}, "kind": "rejected"}]
    counts = {"g": dict(candidates=2, admitted=1, rejected=1, termination="episode_horizon")}
    validate_collection_counts(["g"], rows, counts, 3)
    with pytest.raises(ValueError):
        validate_collection_counts(["g"], rows[:1], counts, 3)
    corrupt = copy.deepcopy(rows)
    corrupt[1]["candidate"]["candidate_id"] = "c0"
    with pytest.raises(ValueError):
        validate_collection_counts(["g"], corrupt, counts, 3)


def test_literal_collection_journal_replay_and_label_lineage():
    from src.data.semantic_collection import setup_collection_environment
    from src.semantic_pipeline.workflow import replay_journal
    component = dict(component_id="g", namespace="n", split="train", start_time_us=T,
                     mixed=False, attack_start=4, attack_length=24, family="slow_drain")
    data = dict(components=[component], entities=[
        dict(component_id="g", namespace="n", split="train", account_id="a", vpa_id="a@upi",
             initial_balance_paise=1000000, created_time_us=1767139200000000, merchant=False),
        dict(component_id="g", namespace="n", split="train", account_id="b", vpa_id="b@upi",
             initial_balance_paise=1000000, created_time_us=1767139200000000, merchant=False)])
    env = setup_collection_environment(component, data["entities"])
    records = [admit_candidate(env, Candidate("c0", "g", "n", 0, T,
                                             "a@upi", "b@upi", 100, 0, "benign")),
               admit_candidate(env, Candidate("c1", "g", "n", 1, T,
                                             "a@upi", "b@upi", 1000001, 0, "benign"))]
    admitted, excluded = replay_journal(data, records, load_config())
    assert len(admitted) == len(excluded) == 1
    assert admitted[0]["features"] == [1., 12., 0., 1.]
    corrupted = copy.deepcopy(records)
    corrupted[0]["label"]["target"] = 1
    with pytest.raises(ValueError):
        replay_journal(data, corrupted, load_config())


def test_remaining_workflow_denials_do_not_touch_rng_estimator_or_output(tmp_path, monkeypatch):
    from src.semantic_pipeline import workflow, review
    from src.detectors import semantic_train
    def forbidden(*a, **k):
        pytest.fail("Execution crossed implementation-only boundary")
    monkeypatch.setattr(np.random, "PCG64", forbidden)
    monkeypatch.setattr(semantic_train, "_estimator", forbidden)
    functions = [workflow.collect, workflow.validate_dataset, review.verify_preservation,
                 review.compare_repeats, review.close_review, review.validate_readiness,
                 semantic_train.validate_model]
    for function in functions:
        kwargs = dict(execution_id="none", root=tmp_path, permit=None)
        if function.__name__ in ("compare_repeats", "close_review"):
            kwargs["other_execution_id"] = "other"
        if function.__name__ in ("validate_readiness", "validate_model"):
            kwargs["detector"] = "xgboost"
        with pytest.raises(ExecutionDenied):
            function(load_config(), **kwargs)
    assert list(tmp_path.iterdir()) == []
