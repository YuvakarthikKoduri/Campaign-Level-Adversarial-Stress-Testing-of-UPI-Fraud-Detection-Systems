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
    second_static = static_a.choose_action(c, {}, ACCOUNTS)
    assert second_static == static_b.choose_action(c, {}, ACCOUNTS)
    assert adaptive.choose_action(c, {}, ACCOUNTS)["amount"] != second_static["amount"]


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
    bad = action(1000)
    bad["from_vpa"] = "outsider@upi"
    actor = ScriptedAttacker([bad])
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


@pytest.mark.parametrize("score,decision", [(0.3999, "ALLOW"), (0.4, "FLAG"),
                                           (0.6999, "FLAG"), (0.7, "BLOCK")])
def test_threshold_boundaries(score, decision):
    assert UPIEnvironment(fraud_detector=ConstantDetector(score)).process_transaction(action())["decision"] == decision


def test_label_only_actions_invariant_to_internal_score():
    histories, actions = [], []
    for score in (0.01, 0.39):
        detector = ConstantDetector(score)
        env = UPIEnvironment(fraud_detector=detector)
        c = campaign()
        c.campaign_id = "same"
        actor = AdaptiveAttacker("unknown")
        CampaignExecutor(detector, env, actor, max_steps=4).execute_campaign(c, ACCOUNTS, seed=8)
        histories.append(actor.history)
        actions.append([{k: t[k] for k in ("from_vpa", "to_vpa", "amount", "timestamp")}
                        for t in c.transactions])
    assert histories[0] == histories[1] and actions[0] == actions[1]


def test_score_feedback_is_explicit_and_does_not_expose_features():
    env = UPIEnvironment(fraud_detector=ConstantDetector())
    actor = AdaptiveAttacker("unknown")
    CampaignExecutor(env.fraud_detector, env, actor, 1, feedback="score").execute_campaign(
        campaign(), ACCOUNTS, seed=1)
    assert actor.history[0]["risk_score"] == 0.1
    assert "features" not in actor.history[0]


def test_stopping_budget_and_time_termination_are_explicit():
    for actions, budget, duration, expected in [
        ([], 500000, 86400, "attacker_stopped"),
        ([action()], 500, 86400, "budget_exhausted"),
        ([action(when=START + timedelta(hours=2))], 500000, 1, "time_horizon"),
    ]:
        env = UPIEnvironment(fraud_detector=ConstantDetector())
        c = campaign()
        c.budget, c.max_duration_seconds = budget, duration
        CampaignExecutor(env.fraud_detector, env, ScriptedAttacker(actions)).execute_campaign(c, ACCOUNTS, seed=1)
        assert c.termination_reason == expected and c.is_complete()
        assert not env.transactions


def test_failed_run_has_failed_manifest_not_valid_canonical(tmp_path, monkeypatch):
    import run_experiment
    monkeypatch.setattr(run_experiment, "load_detector",
                        lambda _: (_ for _ in ()).throw(RuntimeError("inference setup failed")))
    with pytest.raises(RuntimeError):
        run_experiment.main(["--campaigns", "1", "--output-dir", str(tmp_path), "--run-id", "failed"])
    root = tmp_path / "failed"
    assert json.loads((root / "manifest.json").read_text())["status"] == "failed"
    assert not (root / "canonical.json").exists()


def test_benign_traffic_always_block_cannot_be_cost_free():
    observations = []
    for score in (0.01, 0.99):
        env = UPIEnvironment(fraud_detector=ConstantDetector(score))
        c = campaign()
        c.is_fraud = False
        actor = ScriptedAttacker([action(100)])
        CampaignExecutor(env.fraud_detector, env, actor, 1).execute_campaign(c, ACCOUNTS, seed=1)
        observations.append(CampaignMetrics.generate_summary([c]))
    assert observations[0]["legitimate_transaction_block_rate"] == 0
    assert observations[1]["legitimate_transaction_block_rate"] == 1
    assert observations[1]["legitimate_amount_blocked"] == 100


def test_timer_reset_and_monotonicity():
    from src.campaigns.timing import CampaignTimer, TIMING_MODELS
    timer = CampaignTimer(CampaignFamily.SLOW_DRAIN, start_time=START, seed=1)
    a = [timer.next_transaction_time() for _ in range(20)]
    timer.reset()
    b = [timer.next_transaction_time() for _ in range(20)]
    assert a == b and a == sorted(a) and a[0] == START
    model = TIMING_MODELS[CampaignFamily.SLOW_DRAIN]
    assert all(model.min_interval_seconds <= (v - u).total_seconds() <= model.max_interval_seconds
               for u, v in zip(a, a[1:]))


def test_custom_policy_preserved_in_fresh_environments():
    from src.environment.thresholds import ThresholdConfig
    from src.experiments.config import RunConfig
    detector = ConstantDetector(0.5)
    env = UPIEnvironment(ThresholdConfig(0.6, 0.8), detector)
    scenarios = ExperimentScenarios(detector, env)
    result = scenarios.run_scenario_s1(2, seed=5)
    assert result["blocked_campaigns"] == 0
    assert all(t["decision"] == "ALLOW" for r in scenarios.records["S1"] for t in r["transactions"])
    mismatched = ExperimentScenarios(detector, env, config=RunConfig(campaigns=2, seed=5))
    with pytest.raises(ValueError, match="policy"):
        mismatched.run_scenario_s1(2, seed=5)


def test_policy_rejects_extra_schema_inputs_and_nonfinite_probability():
    for score in (float("nan"), float("inf"), -0.1, 1.1):
        env = UPIEnvironment(fraud_detector=ConstantDetector(score))
        with pytest.raises(RuntimeError):
            env.process_transaction(action())
        assert not env.accounts and not env.transactions


def test_baseline_feature_order_is_identical_for_dict_order():
    from src.detectors.baseline import load_detector
    detector = load_detector("models/baseline_xgboost.pkl")
    valid = dict(amount=100, hour_of_day=12, velocity_1h=0, is_new_vpa=1)
    assert detector.predict(valid) == detector.predict(dict(reversed(list(valid.items()))))


def test_loaded_detector_uses_deterministic_inference_threads():
    from src.detectors.baseline import load_detector
    for name in ("xgboost", "random_forest"):
        detector = load_detector(f"models/baseline_{name}.pkl")
        assert detector.model.get_params()["n_jobs"] == 1
