"""Literal helper fixtures only; never call the causal generation workflow."""
import hashlib
import json
from dataclasses import replace

import pytest

from src.semantic_pipeline.config import load_config, DEFAULT_CONFIG
from src.semantic_pipeline.authorization import ExecutionDenied
from src.data.semantic_entities import derive_seed, generate_entities
from src.data.semantic_generator import Candidate, generate_candidates
from src.data.semantic_collection import CollectionObserver, GateCEnvironment, admit_candidate

T = 1767614400000000


def config():
    return load_config(DEFAULT_CONFIG)


def environment():
    env = GateCEnvironment("literal", CollectionObserver(), purpose="collection")
    for name in ("a", "b"):
        env.create_account(name, 1000)
        env.create_vpa(name + "@upi", name, name)
    return env


def candidate(**changes):
    base = Candidate("candidate0", "component0", "literal", 0, T,
                     "a@upi", "b@upi", 10001, 1, "slow_drain")
    return replace(base, **changes)


def test_versioned_configuration_and_seed_contract():
    c = config()
    assert c.data["profiles"]["baseline"]["components"] == 1000
    assert c.data["profiles"]["pilot"]["components"] == 24
    assert c.data["policy"]["benign_block_budget"] == .01
    payload = json.dumps(["upi-gc-seed-v1", 42026, "entity", "component0"],
                         separators=(",", ":"), sort_keys=True).encode()
    assert derive_seed(42026, "entity", "component0") == int.from_bytes(
        hashlib.sha256(payload).digest()[:16], "big")
    assert derive_seed(42026, "entity", "component0") != derive_seed(42026, "time", "component0")
    assert c.digest == config().digest
    altered = c.data
    altered["models"]["random_forest"]["n_estimators"] = 301
    from src.semantic_pipeline.config import PipelineConfig
    other = PipelineConfig.from_dict(altered)
    assert other.generation_digest == c.generation_digest
    assert other.digest != c.digest


@pytest.mark.parametrize("function", [generate_entities, generate_candidates])
def test_generation_interfaces_deny_without_approval(function):
    with pytest.raises(ExecutionDenied):
        function(config(), execution_id="unapproved", permit=None)


def test_literal_admission_label_separation_and_all_allow_observer():
    a, b = environment(), environment()
    first = admit_candidate(a, candidate())
    altered = admit_candidate(b, candidate(intent=0, family="benign"))
    assert first["features"] == altered["features"] == [100.01, 12., 0., 1.]
    assert first["label"]["target"] == 1 and altered["label"]["target"] == 0
    assert first["outcome"]["fraud_probability"] is None
    assert first["outcome"]["collector_score"] == 0
    assert first["outcome"]["decision"] == "ALLOW"
    assert "intent" not in first["event"]
    second = admit_candidate(a, candidate(candidate_id="candidate1", candidate_seq=1))
    assert second["features"][2:] == [1., 0.]


@pytest.mark.parametrize("change", [{"amount_paise": -1}, {"amount_paise": 100001},
                                  {"source_vpa_id": "unknown@upi"}])
def test_invalid_literal_action_has_no_history_or_ledger_commit(change):
    env = environment()
    original = env._state
    result = admit_candidate(env, candidate(**change))
    assert result["kind"] == "rejected" and result["features"] is None
    assert env._state is original and env.history.next_sequence == 0


def test_journal_failure_invalidates_and_restores_whole_admission():
    env = environment()
    original = env._state

    def fail(record):
        raise OSError("literal partial journal failure")

    with pytest.raises(Exception):
        admit_candidate(env, candidate(), journal_append=fail)
    assert env.run_invalid and env._state is original


def test_fixture_only_gate_b_default_remains_closed():
    from src.environment.semantic import SemanticEnvironment
    with pytest.raises(ValueError):
        SemanticEnvironment("literal", CollectionObserver())
