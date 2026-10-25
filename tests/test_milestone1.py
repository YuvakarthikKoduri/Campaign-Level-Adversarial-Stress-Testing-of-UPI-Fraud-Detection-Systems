"""Regression gates for corrected-v2, using deterministic hand-calculated fixtures."""
import copy
import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.attackers.adaptive import AdaptiveAttacker
from src.campaigns.executor import CampaignExecutor
from src.campaigns.generator import CampaignGenerator, CampaignFamily
from src.environment import UPIEnvironment
from src.environment.entities import Transaction
from src.evaluation.metrics import CampaignMetrics
from src.experiments.scenarios import ExperimentScenarios

START = datetime(2026, 1, 5, 12)
ACCOUNTS = ["a@upi", "b@upi", "c@upi"]


class ConstantDetector:
    def __init__(self, score=0.1):
        self.score = score
        self.inputs = []

    def predict(self, features):
        self.inputs.append(dict(features))
        return self.score


class ScriptedAttacker:
    def __init__(self, actions):
        self.actions = iter(actions)
        self.history = []

    def choose_action(self, campaign, state, accounts):
        # No privileged detector history may arrive through a campaign object.
        assert not hasattr(campaign, "transactions")
        return next(self.actions, None)

    def observe(self, response):
        self.history.append(response)


def action(amount=1000, when=START, **extra):
    return dict(from_vpa="a@upi", to_vpa="b@upi", amount=amount, timestamp=when, **extra)


def campaign():
    c = CampaignGenerator().create_known_fraud_campaign(target_amount=100000)
    c.created_at = START
    return c


@pytest.mark.parametrize("score,decision,moved", [(0.1, "ALLOW", 1000),
                                                  (0.5, "FLAG", 1000),
                                                  (0.9, "BLOCK", 0)])
def test_execution_and_campaign_accounting(score, decision, moved):
    env = UPIEnvironment(fraud_detector=ConstantDetector(score))
    c = campaign()
    response = env.process_transaction(action())
    c.add_transaction({**action(), **response})
    assert response["decision"] == decision
    assert response["amount_transferred"] == moved
    assert c.total_amount_moved == moved
    assert c.total_amount_blocked == (1000 if decision == "BLOCK" else 0)
    assert env.get_account_balance("a@upi") == 500000 - moved
    assert env.get_account_balance("b@upi") == 500000 + moved


def test_flag_exposure_and_success():
    env = UPIEnvironment(fraud_detector=ConstantDetector(0.5))
    c = campaign()
    c.target_amount = 1000
    response = env.process_transaction(action())
    c.add_transaction({**action(), **response})
    assert c.is_complete() and c.status.value == "SUCCESS"
    assert c.detection_time == 0 and c.intervention_time is None
    assert c.exposure_before_detection == 0


def test_event_clock_not_runtime():
    c = campaign()
    c.add_transaction({**action(when=START + timedelta(hours=1)),
                       "decision": "BLOCK", "status": "blocked", "amount_transferred": 0})
    assert c.detection_time == c.intervention_time == 3600
    assert c.completed_at == START + timedelta(hours=1)


def test_first_observed_source_vpa_is_pretransaction():
    env = UPIEnvironment(fraud_detector=ConstantDetector())
    first = env.process_transaction(action())
    second = env.process_transaction(action(when=START + timedelta(seconds=1)))
    assert first["features"]["is_new_vpa"] == 1
    assert second["features"]["is_new_vpa"] == 0
    assert [first["features"]["velocity_1h"], second["features"]["velocity_1h"]] == [0, 1]


def test_velocity_excludes_future_and_lower_boundary():
    env = UPIEnvironment(fraud_detector=ConstantDetector())
    for when in [START + timedelta(seconds=1), START - timedelta(hours=1),
                 START - timedelta(seconds=1)]:
        env.transactions.append(Transaction(**action(when=when)))
    features = env._compute_upi_features(Transaction(**action()))
    assert features["velocity_1h"] == 1


def test_detector_error_is_fatal_and_has_no_mutation():
    class Broken:
        def predict(self, features):
            raise ValueError("deliberate inference failure")
    env = UPIEnvironment(fraud_detector=Broken())
    with pytest.raises(RuntimeError, match="inference"):
        env.process_transaction(action())
    assert not env.accounts and not env.transactions and not env.vpas


@pytest.mark.parametrize("amount", [float("nan"), float("inf"), -1, 0])
def test_invalid_amounts_do_not_mutate(amount):
    env = UPIEnvironment(fraud_detector=ConstantDetector())
    response = env.process_transaction(action(amount))
    assert response["execution_status"] == "invalid"
    assert response["amount_transferred"] == 0 and not env.accounts


def test_inactive_recipient_cannot_destroy_money():
    env = UPIEnvironment(fraud_detector=ConstantDetector())
    for name in ACCOUNTS:
        env.create_account(name, 5000)
        env.create_vpa(name, name, name)
    env.accounts["b@upi"].is_active = False
    response = env.process_transaction(action())
    assert response["amount_transferred"] == 0
    assert env.accounts["a@upi"].balance == env.accounts["b@upi"].balance == 5000


def test_horizon_is_terminal_and_censored():
    env = UPIEnvironment(fraud_detector=ConstantDetector())
    c = campaign()
    actor = ScriptedAttacker([action()])
    CampaignExecutor(env.fraud_detector, env, actor, max_steps=1).execute_campaign(c, ACCOUNTS, seed=9)
    assert c.status.value == "TIMED_OUT" and c.termination_reason == "step_horizon"
    summary = CampaignMetrics.generate_summary([c])
    assert summary["avg_detection_time_sec"] is None
    assert summary["detection_censored_campaigns"] == 1


def test_executor_feedback_is_complete_and_label_only():
    env = UPIEnvironment(fraud_detector=ConstantDetector())
    c = campaign()
    actor = AdaptiveAttacker("known")
    CampaignExecutor(env.fraud_detector, env, actor, max_steps=1).execute_campaign(c, ACCOUNTS, seed=9)
    assert actor.safe_amounts and actor.safe_beneficiaries
    feedback = actor.history[0]
    assert {"from_vpa", "to_vpa", "amount", "timestamp", "decision", "amount_transferred"} <= feedback.keys()
    assert not {"risk_score", "features", "details", "threshold"} & feedback.keys()


def test_out_of_order_campaign_action_is_invalid_not_a_detector_block():
    env = UPIEnvironment(fraud_detector=ConstantDetector())
    c = campaign()
    actor = ScriptedAttacker([action(when=START - timedelta(seconds=1))])
    CampaignExecutor(env.fraud_detector, env, actor).execute_campaign(c, ACCOUNTS, seed=1)
    assert c.status.value == "INVALID"
    assert c.detection_time is None and c.intervention_time is None
    assert not env.transactions


def test_generated_workload_is_deterministic_and_global_rng_independent():
    from src.experiments.config import RunConfig, build_workload
    import random
    config = RunConfig(seed=999, campaigns=6)
    a = build_workload(config)
    random.seed(1)
    for _ in range(100):
        random.random()
    assert a == build_workload(config)
    assert a != build_workload(RunConfig(seed=998, campaigns=6))
    assert {s.family for s in a["unknown"]} == {
        "slow_drain", "gradual_escalation", "beneficiary_hopping"}


@pytest.mark.parametrize("family", list(CampaignFamily))
def test_family_static_ignores_feedback_and_adaptive_responds(family):
    from src.attackers.family_based import make_attacker
    c = campaign()
    c.family = family
    static_a = make_attacker(family, adaptive=False, seed=77)
    static_b = make_attacker(family, adaptive=False, seed=77)
    adaptive = make_attacker(family, adaptive=True, seed=77)
    initial = [a.choose_action(c, {}, ACCOUNTS) for a in [static_a, static_b, adaptive]]
    assert initial[0] == initial[1] == initial[2]
    static_a.observe({"decision": "ALLOW", "amount": initial[0]["amount"], "to_vpa": "b@upi"})
    static_b.observe({"decision": "FLAG", "amount": initial[0]["amount"], "to_vpa": "b@upi"})
    adaptive.observe({"decision": "FLAG", "amount": initial[0]["amount"], "to_vpa": "b@upi"})
    assert static_a.choose_action(c, {}, ACCOUNTS) == static_b.choose_action(c, {}, ACCOUNTS)
    assert adaptive.choose_action(c, {}, ACCOUNTS)["amount"] != static_a.choose_action(c, {}, ACCOUNTS)["amount"]


def test_pairing_and_repeat_semantic_outputs():
    from src.experiments.config import RunConfig, build_workload
    config = RunConfig(seed=123, campaigns=3, max_steps=6)
    workload = build_workload(config)
    outcomes = []
    for score in [0.1, 0.9, 0.1]:
        detector = ConstantDetector(score)
        scenarios = ExperimentScenarios(detector, UPIEnvironment(fraud_detector=detector),
                                        config=config, workload=workload)
        scenarios.run_all_scenarios(3, save_results=False, seed=123)
        outcomes.append(copy.deepcopy(scenarios.records))
    assert outcomes[0] == outcomes[2]
    for scenario in ["S1", "S2", "S3", "S4"]:
        assert [c["spec"] for c in outcomes[0][scenario]] == [
            c["spec"] for c in outcomes[1][scenario]]
    assert [c["spec"] for c in outcomes[0]["S1"]] == [c["spec"] for c in outcomes[0]["S2"]]
    assert [c["spec"] for c in outcomes[0]["S3"]] == [c["spec"] for c in outcomes[0]["S4"]]


def test_run_output_refuses_overwrite_and_has_manifest(tmp_path):
    from src.experiments.config import RunConfig
    import run_experiment
    args = ["--scenario", "all", "--detector", "both", "--campaigns", "3",
            "--seed", "999", "--output-dir", str(tmp_path), "--run-id", "paired"]
    run_experiment.main(args)
    root = tmp_path / "paired"
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["config"]["seed"] == 999
    assert manifest["status"] == "complete" and manifest["model_sha256"]
    assert manifest["metric_version"] == "corrected-v2"
    before = (root / "manifest.json").read_bytes()
    with pytest.raises(FileExistsError):
        run_experiment.main(args)
    assert (root / "manifest.json").read_bytes() == before


def test_detector_feature_schema_rejects_labels_and_nonfinite():
    from src.detectors.baseline import load_detector
    detector = load_detector("models/baseline_xgboost.pkl")
    valid = dict(amount=100, hour_of_day=12, velocity_1h=0, is_new_vpa=1)
    for extra in [{"scenario": "S1"}, {"is_fraud": 1}, {"amount": float("nan")},
                  {"velocity_1h": -1}, {"is_new_vpa": 2}]:
        with pytest.raises(ValueError):
            detector.predict({**valid, **extra})


def test_action_threat_model_rejects_uncontrolled_sources_and_budget():
    env = UPIEnvironment(fraud_detector=ConstantDetector())
    c = campaign()
    c.budget = 500
    actor = ScriptedAttacker([action(1000, from_override="outsider@upi")])
    CampaignExecutor(env.fraud_detector, env, actor).execute_campaign(c, ACCOUNTS, seed=1)
    assert c.status.value == "INVALID" and not env.accounts


def test_benign_false_positive_and_money_fields():
    c = campaign()
    c.is_fraud = False
    c.add_transaction({**action(), "decision": "BLOCK", "status": "blocked",
                       "amount_transferred": 0})
    summary = CampaignMetrics.generate_summary([c])
    assert summary["legitimate_transaction_block_rate"] == 1
    assert summary["legitimate_amount_blocked"] == 1000
    assert summary["total_attempted_amount"] == 1000


def test_runconfig_validates_limits_and_development_eval_separation():
    from src.experiments.config import RunConfig
    for kwargs in [{"campaigns": 0}, {"max_steps": 0}, {"max_duration_seconds": -1},
                   {"split": "evaluation", "development_seeds": (42,), "seed": 42}]:
        with pytest.raises(ValueError):
            RunConfig(**kwargs)
