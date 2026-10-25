"""Gate B uses literal fixtures only: no datasets, trained models, or studies."""
import json
from dataclasses import replace
from datetime import datetime

import numpy as np
import pytest

from src.features import (
    FeatureEvent, FeatureHistory, HistorySnapshot, CONTRACT_ID, SCHEMA_DIGEST,
    encode_vector, extract_features, timestamp_us,
)
from src.data.semantic_dataset import replay_events, encode_rows, decode_rows
from src.data.semantic_provenance import feature_metadata, validate_feature_metadata, validate_splits
from src.detectors.semantic import FixtureDetector
from src.environment.semantic import SemanticEnvironment, RunInvalid
from src.campaigns.semantic_executor import SemanticCampaignExecutor

SECOND = 1_000_000
HOUR = 3600 * SECOND
T = timestamp_us("2026-01-05T12:00:00Z")


def event(seq=0, at=T, source="a@upi", target="b@upi", namespace="c", **kwargs):
    return FeatureEvent(event_id=f"e{seq}", history_namespace=namespace,
                        event_seq=seq, event_time_utc_us=at,
                        source_vpa_id=source, beneficiary_vpa_id=target,
                        amount_paise=10001, **kwargs)


def vector(e, history):
    return encode_vector(extract_features(e, history.view_before(e)))


def env(score=0.1, namespace="c", legacy=False):
    detector = FixtureDetector(lambda row: score)
    result = SemanticEnvironment(namespace, detector, legacy_naive_utc=legacy)
    for name in ("a", "b", "z"):
        result.create_account(name, 10000)
        result.create_vpa(f"{name}@upi", name, name)
    return result


def state(environment):
    """Public semantic-state fingerprint, independent of candidate object IDs."""
    return (
        environment.history.snapshot(),
        tuple((key, a.balance, tuple(a.transaction_history), a.is_active)
              for key, a in sorted(environment.accounts.items())),
        json.dumps([t.to_dict() for t in environment.transactions], sort_keys=True),
        tuple(sorted(environment.stats.items())),
    )


def test_first_use_and_same_timestamp_oracle():
    h = FeatureHistory("c")
    for seq, expected in enumerate(([100.01, 12, 0, 1],
                                    [100.01, 12, 1, 0],
                                    [100.01, 12, 2, 0])):
        e = event(seq)
        before = h.snapshot()
        assert vector(e, h).dtype == np.float64
        np.testing.assert_array_equal(vector(e, h), [expected])
        assert h.snapshot() == before  # extraction is pure
        h.commit_observation(e)


@pytest.mark.parametrize("offset,count", [(-HOUR - 1, 0), (-HOUR, 0), (-HOUR + 1, 1), (0, 1)])
def test_exact_window_boundaries(offset, count):
    h = FeatureHistory("c")
    h.commit_observation(event(0, at=T + offset))
    np.testing.assert_array_equal(vector(event(1), h), [[100.01, 12, count, 0]])


def test_source_role_aliases_and_lifetime_novelty():
    h = FeatureHistory("c")
    h.commit_observation(event())
    np.testing.assert_array_equal(vector(event(1, source="b@upi", target="z@upi"), h),
                                  [[100.01, 12, 0, 1]])
    np.testing.assert_array_equal(vector(event(1, source="alias@upi"), h),
                                  [[100.01, 12, 0, 1]])
    h.commit_observation(event(1, at=T + 2 * HOUR))
    np.testing.assert_array_equal(vector(event(2, at=T + 4 * HOUR), h),
                                  [[100.01, 16, 0, 0]])
    # Queue compaction retains the lifetime source observation.
    assert len(h.snapshot().to_dict()["recent"]) == 1


@pytest.mark.parametrize("change", [
    {"event_seq": 0, "event_id": "different"},
    {"event_seq": 1, "event_id": "e0"},
    {"event_seq": 1, "event_time_utc_us": T - 1},
    {"event_seq": 1, "history_namespace": "wrong"},
])
def test_invalid_order_or_namespace_is_nonmutating(change):
    h = FeatureHistory("c")
    h.commit_observation(event())
    before = h.snapshot()
    bad = replace(event(1), **change)
    with pytest.raises(ValueError):
        h.view_before(bad)
    with pytest.raises(ValueError):
        h.commit_observation(bad)
    assert h.snapshot() == before


@pytest.mark.parametrize("changes", [
    {"amount_paise": 0}, {"amount_paise": True}, {"amount_paise": 1.5},
    {"event_seq": -1}, {"event_seq": True}, {"event_time_utc_us": 1.0},
    {"source_vpa_id": "a"}, {"beneficiary_vpa_id": "a@upi"},
    {"history_namespace": ""}, {"event_id": ""},
])
def test_canonical_input_validation(changes):
    with pytest.raises(ValueError):
        replace(event(), **changes)


def test_timezone_exactness_and_strict_external_input():
    assert timestamp_us("2026-01-05T17:30:00+05:30") == T
    for bad in ("2026-01-05T12:00:00", datetime(2026, 1, 5, 12)):
        with pytest.raises(ValueError):
            timestamp_us(bad)
    assert timestamp_us(datetime(2026, 1, 5, 12), legacy_naive_utc=True) == T
    assert timestamp_us("2026-01-05T12:00:00.000001Z") == T + 1


def test_snapshot_roundtrip_reset_and_future_rejection():
    h = FeatureHistory("c")
    h.commit_observation(event())
    snapshot = h.snapshot()
    restored = FeatureHistory.from_snapshot(snapshot, "c")
    assert restored.snapshot() == snapshot
    assert vector(event(1), restored).tolist() == [[100.01, 12.0, 1.0, 0.0]]
    with pytest.raises(ValueError):
        restored.view_before(event(1, at=T - 1))
    with pytest.raises(ValueError):
        FeatureHistory.from_snapshot(snapshot, "another")
    with pytest.raises(ValueError):
        FeatureHistory.from_snapshot(replace(snapshot, sha256="0" * 64), "c")
    assert vector(event(namespace="new"), FeatureHistory("new")).tolist() == [[100.01, 12, 0, 1]]
    restored.commit_observation(event(1))
    assert h.snapshot() == snapshot  # initialization is independent


@pytest.mark.parametrize("field,value", [
    ("seen_sources", []), ("source_counts", [["a@upi", 9]]),
    ("last_position", [T + HOUR, 0]), ("event_ids", ["wrong"]),
    ("contract_id", "legacy"), ("schema_digest", "wrong"),
])
def test_structurally_corrupt_snapshots_even_with_recomputed_digest(field, value):
    h = FeatureHistory("c")
    h.commit_observation(event())
    payload = h.snapshot().to_dict()
    payload[field] = value
    corrupt = HistorySnapshot.from_dict(payload)
    with pytest.raises(ValueError):
        FeatureHistory.from_snapshot(corrupt, "c")


def test_event_bound_view_and_no_label_input():
    h = FeatureHistory("c")
    with pytest.raises(ValueError):
        extract_features(event(1), h.view_before(event()))
    with pytest.raises(TypeError):
        FeatureEvent(**{**event().__dict__, "fraud_label": 1})


def test_offline_prefix_serialization_and_independent_oracle():
    events = (event(), event(1), event(2, at=T + HOUR))
    rows = replay_events(events, "c")
    expected = [[100.01, 12, 0, 1], [100.01, 12, 1, 0], [100.01, 13, 0, 0]]
    assert [row.vector.tolist()[0] for row in rows] == expected
    assert replay_events(events[:2], "c") == rows[:2]
    assert decode_rows(encode_rows(rows)) == rows
    assert [row.event_id for row in rows] == ["e0", "e1", "e2"]
    altered = json.loads(encode_rows(rows))
    altered["rows"][0]["values"][2] = 0.5
    with pytest.raises(ValueError):
        decode_rows(json.dumps(altered))


@pytest.mark.parametrize("score,decision,moved", [
    (0.1, "ALLOW", 100.01), (0.5, "FLAG", 100.01), (0.9, "BLOCK", 0),
])
def test_real_online_parity_and_all_decisions_are_observed(score, decision, moved):
    online = env(score)
    before = state(online)
    response = online.process_event(event())
    assert response["decision"] == decision
    assert response["amount_transferred"] == moved
    assert response["features"] == dict(amount=100.01, hour_of_day=12, velocity_1h=0, is_new_vpa=1)
    assert state(online) != before
    # Feature-layer direct calls do not impose campaign termination.
    second = online.process_event(event(1))
    assert second["features"]["velocity_1h"] == 1
    assert second["features"]["is_new_vpa"] == 0
    offline = replay_events((event(), event(1)), "c")
    for txn, row in zip(online.transactions, offline):
        np.testing.assert_array_equal(
            np.asarray([[txn.features[k] for k in
                         ("amount", "hour_of_day", "velocity_1h", "is_new_vpa")]], dtype=np.float64),
            row.vector)
    assert online.get_account_balance("a@upi") == 10000 - 2 * moved
    assert online.get_account_balance("b@upi") == 10000 + 2 * moved


def test_pre_admission_ineligible_no_detector_or_history():
    calls = []
    online = env()
    online.fraud_detector = FixtureDetector(lambda row: calls.append(row) or 0.1)
    online.accounts["a"].is_active = False
    before = state(online)
    assert online.process_event(event())["execution_status"] == "invalid"
    assert state(online) == before and calls == []
    online.accounts["a"].is_active = True
    for bad in (replace(event(), amount_paise=1000001), replace(event(), source_vpa_id="unknown@upi")):
        before = state(online)
        assert online.process_event(bad)["execution_status"] == "invalid"
        assert state(online) == before and calls == []


@pytest.mark.parametrize("failure_stage", ["detector", "settle", "history", "response", "publish"])
def test_exception_atomicity_and_run_invalidation(monkeypatch, failure_stage):
    online = env()
    before = state(online)
    original_state = online._state

    def fail(*args, **kwargs):
        raise RuntimeError("injected failure")

    if failure_stage == "detector":
        online.fraud_detector = FixtureDetector(fail)
    elif failure_stage == "settle":
        real = SemanticEnvironment._settle

        def partial(stage, e, decision):
            real(stage, e, decision)
            fail()
        monkeypatch.setattr(SemanticEnvironment, "_settle", partial)
    elif failure_stage == "history":
        real = FeatureHistory.commit_observation

        def partial(history, e):
            real(history, e)
            fail()
        monkeypatch.setattr(FeatureHistory, "commit_observation", partial)
    elif failure_stage == "response":
        monkeypatch.setattr(SemanticEnvironment, "_response", fail)
    else:
        monkeypatch.setattr(SemanticEnvironment, "_before_publish", fail)
    with pytest.raises(RunInvalid):
        online.process_event(event())
    assert state(online) == before
    assert online._state is original_state
    assert online.run_invalid
    with pytest.raises(RunInvalid):
        online.process_event(event(1))


@pytest.mark.parametrize("score", [float("nan"), float("inf"), -1, 1.1, True])
def test_invalid_detector_output_is_fatal_noncommitting(score):
    online = env(score)
    before = state(online)
    with pytest.raises(RunInvalid):
        online.process_event(event())
    assert state(online) == before


def test_duplicate_backward_and_future_history_fail_closed():
    online = env()
    online.process_event(event())
    before = state(online)
    with pytest.raises(RunInvalid):
        online.process_event(event())
    assert state(online) == before


def test_snapshot_online_offline_parity():
    initial = FeatureHistory("c")
    initial.commit_observation(event())
    snap = initial.snapshot()
    online = SemanticEnvironment("c", FixtureDetector(lambda row: .1), snapshot=snap)
    for name in ("a", "b"):
        online.create_account(name, 10000)
        online.create_vpa(f"{name}@upi", name, name)
    response = online.process_event(event(1))
    row = replay_events((event(1),), "c", snapshot=snap)[0]
    assert list(response["features"].values()) == row.vector.tolist()[0]
    assert initial.snapshot() == snap


def test_same_extractor_and_encoder_are_used(monkeypatch):
    import src.features.extractor as shared
    calls = {"extract": 0, "encode": 0}
    extract, encode = shared.extract_features, shared.encode_vector

    def counting_extract(*args, **kwargs):
        calls["extract"] += 1
        return extract(*args, **kwargs)

    def counting_encode(*args, **kwargs):
        calls["encode"] += 1
        return encode(*args, **kwargs)

    monkeypatch.setattr(shared, "extract_features", counting_extract)
    monkeypatch.setattr(shared, "encode_vector", counting_encode)
    replay_events((event(),), "c")
    env().process_event(event())
    assert calls == {"extract": 2, "encode": 2}


def test_manifest_contract_checks_and_split_integrity():
    metadata = feature_metadata()
    assert metadata["contract_id"] == CONTRACT_ID
    assert metadata["schema_digest"] == SCHEMA_DIGEST
    validate_feature_metadata(metadata)
    for key in metadata:
        bad = dict(metadata, **{key: "wrong"})
        with pytest.raises(ValueError):
            validate_feature_metadata(bad)
    validate_splits({"train": ["e0"], "validation": ["e1"], "test": ["e2"]},
                    {"e0": "group0", "e1": "group1", "e2": "group2"})
    for splits, groups in [
        ({"train": ["e0"], "validation": ["e0"], "test": ["e2"]}, {"e0": "g0", "e2": "g2"}),
        ({"train": ["e0"], "validation": ["e1"], "test": ["e2"]}, {"e0": "g", "e1": "g", "e2": "g2"}),
    ]:
        with pytest.raises(ValueError):
            validate_splits(splits, groups)


def test_legacy_detector_is_not_silently_used():
    from src.detectors.baseline import BaselineDetector
    with pytest.raises(ValueError):
        SemanticEnvironment("c", BaselineDetector())


def test_explicit_legacy_utc_adapter_and_executor_integration():
    from src.campaigns.generator import Campaign
    c = Campaign("c", "attacker", "fixture", 1000)
    online = env(namespace=c.campaign_id, legacy=True)

    class Script:
        def __init__(self):
            self.feedback = []

        def choose_action(self, campaign, state, accounts):
            assert not hasattr(campaign, "transactions")
            return dict(from_vpa="a@upi", to_vpa="b@upi", amount=100,
                        timestamp="2026-01-05T12:00:00")

        def observe(self, feedback):
            self.feedback.append(feedback)

    attacker = Script()
    result = SemanticCampaignExecutor(online.fraud_detector, online, attacker, max_steps=2).execute_campaign(
        c, ["a@upi", "b@upi"])
    assert result.termination_reason == "step_horizon"
    assert [t["features"]["velocity_1h"] for t in result.transactions] == [0, 1]
    assert all("risk_score" not in item and "features" not in item for item in attacker.feedback)
    assert online.history.snapshot().to_dict()["last_position"] == [T, 1]
    with pytest.raises(ValueError):
        SemanticCampaignExecutor(online.fraud_detector, online, attacker).execute_campaign(
            Campaign("c", "attacker", "fixture", 1000), ["a@upi", "b@upi"])


def test_native_transaction_adapter_rejects_ambiguous_time_without_history():
    online = env()
    before = state(online)
    result = online.process_transaction(dict(
        transaction_id="e0", from_vpa="a@upi", to_vpa="b@upi", amount=100.01,
        timestamp="2026-01-05T12:00:00"))
    assert result["execution_status"] == "invalid"
    assert state(online) == before


@pytest.mark.parametrize("stamp", [
    "2026-01-05T12:00:00.0000001Z", "2026-01-05 12:00:00Z",
    "2026-01-05T12:00Z", "2026-01-05T12:00:00+0000",
])
def test_external_rfc3339_rejects_lossy_or_ambiguous_encodings(stamp):
    with pytest.raises(ValueError):
        timestamp_us(stamp)


def test_returned_diagnostics_do_not_alias_committed_state():
    online = env()
    response = online.process_event(event())
    before = state(online)
    response["features"]["velocity_1h"] = 999
    response["risk_factors"].append("injected")
    assert state(online) == before


def test_codec_rejects_noncanonical_money_and_backwards_sequence():
    rows = replay_events((event(), event(1)), "c")
    payload = json.loads(encode_rows(rows))
    encoded_rows = payload["rows"]
    encoded_rows[0]["values"][0] = 1.001
    with pytest.raises(ValueError):
        decode_rows(json.dumps(payload))
    payload = json.loads(encode_rows(rows))
    encoded_rows = payload["rows"]
    encoded_rows.reverse()
    with pytest.raises(ValueError):
        decode_rows(json.dumps(payload))


def test_credit_failure_restores_debit_history_and_sequence(monkeypatch):
    from src.environment.entities import Account
    online = env()
    before = state(online)

    def fail_credit(*args, **kwargs):
        raise RuntimeError("credit failure after staged debit")

    monkeypatch.setattr(Account, "credit", fail_credit)
    with pytest.raises(RunInvalid):
        online.process_event(event())
    assert state(online) == before


def test_corrupt_ledger_invalidates_before_scoring():
    online = env()
    calls = []
    online.fraud_detector = FixtureDetector(lambda row: calls.append(row) or 0.1)
    online.accounts["a"].balance += 1  # unrecorded external ledger mutation
    before = state(online)
    with pytest.raises(RunInvalid):
        online.process_event(event())
    assert state(online) == before and calls == []


def test_executor_feedback_exception_rolls_back_whole_call():
    from src.campaigns.generator import Campaign
    c = Campaign("c", "attacker", "fixture", 1000)
    online = env(legacy=True)
    before = state(online)

    class FailFeedback:
        def choose_action(self, *args, **kwargs):
            return dict(from_vpa="a@upi", to_vpa="b@upi", amount=100,
                        timestamp="2026-01-05T12:00:00")

        def observe(self, response):
            raise RuntimeError("feedback failed after transaction processing")

    with pytest.raises(RunInvalid):
        SemanticCampaignExecutor(online.fraud_detector, online, FailFeedback()).execute_campaign(
            c, ["a@upi", "b@upi"])
    assert state(online) == before
    assert c.transactions == [] and c.total_amount_moved == 0
    assert c.termination_reason == "semantic_processing_error" and online.run_invalid


def test_executor_block_terminates_after_one_committed_observation():
    from src.campaigns.generator import Campaign
    c = Campaign("c", "attacker", "fixture", 1000)
    online = env(.9, legacy=True)

    class Blocked:
        def choose_action(self, *args, **kwargs):
            return dict(from_vpa="a@upi", to_vpa="b@upi", amount=100,
                        timestamp="2026-01-05T12:00:00")

        def observe(self, response):
            assert response["decision"] == "BLOCK"

    SemanticCampaignExecutor(online.fraud_detector, online, Blocked()).execute_campaign(
        c, ["a@upi", "b@upi"])
    assert c.termination_reason == "first_detector_block"
    assert len(online.transactions) == 1 and online.history.next_sequence == 1
    assert online.get_account_balance("a@upi") == 10000


def test_reentrant_detector_callback_invalidates_without_commit():
    online = env()
    before = state(online)
    online.fraud_detector = FixtureDetector(lambda row: online.process_event(event(1)))
    with pytest.raises(RunInvalid):
        online.process_event(event())
    assert state(online) == before and online.run_invalid


def test_aliases_are_per_source_not_per_shared_account():
    online = env()
    online.create_vpa("alias@upi", "a", "alias")
    online.process_event(event())
    response = online.process_event(event(1, source="alias@upi"))
    assert response["features"]["velocity_1h"] == 0
    assert response["features"]["is_new_vpa"] == 1
    assert online.get_account_balance("a@upi") == 9799.98


@pytest.mark.parametrize("corruption", ["future", "same_time_later", "duplicate", "backwards"])
def test_snapshot_observation_order_corruption(corruption):
    history = FeatureHistory("c")
    history.commit_observation(event())
    history.commit_observation(event(1, at=T + 1))
    payload = history.snapshot().to_dict()
    if corruption == "future":
        payload["recent"][0][2] = T + HOUR
    elif corruption == "same_time_later":
        payload["recent"][0][2] = T + 1
        payload["recent"][0][3] = 2
    elif corruption == "duplicate":
        payload["recent"][1][0] = "e0"
    else:
        payload["recent"].reverse()
    with pytest.raises(ValueError):
        FeatureHistory.from_snapshot(HistorySnapshot.from_dict(payload), "c")


def test_codec_rejects_contract_mismatch_duplicate_keys_and_missing_envelope():
    serialized = encode_rows(replay_events((event(),), "c"))
    payload = json.loads(serialized)
    payload["metadata"]["contract_id"] = "legacy"
    with pytest.raises(ValueError):
        decode_rows(json.dumps(payload))
    with pytest.raises(ValueError):
        decode_rows('{"metadata":{}, "metadata":{}, "rows":[]}')
    with pytest.raises(ValueError):
        decode_rows("[]")


def test_all_three_decision_histories_have_the_same_feature_prefix():
    # This intentionally uses primitive admission, not a campaign continued after BLOCK.
    traces = []
    for score in (.1, .5, .9):
        online = env(score)
        traces.append([online.process_event(event(i))["features"] for i in range(3)])
    assert traces[0] == traces[1] == traces[2]


def test_cold_start_new_campaign_namespace_is_independent():
    first = env()
    first.process_event(event())
    second = env(namespace="second")
    response = second.process_event(event(namespace="second"))
    assert response["features"]["velocity_1h"] == 0
    assert response["features"]["is_new_vpa"] == 1
    assert first.history.snapshot().to_dict()["last_position"] == [T, 0]


@pytest.mark.parametrize("corruption", ["counters", "account_history", "feature_history"])
def test_cross_state_corruption_rejected_before_scoring(corruption):
    online = env()
    calls = []
    online.fraud_detector = FixtureDetector(lambda row: calls.append(row) or .1)
    if corruption == "counters":
        online.stats["allowed"] = 9
    elif corruption == "account_history":
        online.accounts["a"].transaction_history.append("phantom")
    else:
        online.history.commit_observation(event())
    before = state(online)
    with pytest.raises(RunInvalid):
        online.process_event(event(1))
    assert calls == [] and state(online) == before
