"""Hand-calculated unit checks and real simulator/detector end-to-end checks."""
import copy
from dataclasses import replace
import json
from pathlib import Path

import pytest

from src.attackers.q_learning import ACTIONS, QLearningAttacker, reward_for
from src.campaigns.executor import AttackerCampaignView
from src.campaigns.generator import CampaignFamily
from src.detectors.baseline import load_detector
from src.experiments.config import RunConfig, build_workload
from src.experiments.prototype import PrototypeConfig, compare, episode, metrics


class Constant:
    def __init__(self, score):
        self.score = score
    def predict(self, features):
        return self.score


def view(target=10000):
    return AttackerCampaignView("unit", target, CampaignFamily.HIGH_VALUE_BURST, "known")


@pytest.mark.parametrize("moved,decision,success,exhausted,expected", [
    (1000, "ALLOW", False, False, .28),
    (1000, "FLAG", False, False, .08),
    (0, "BLOCK", False, False, -1.02),
    (10000, "ALLOW", True, False, 4.98),
    (0, "ALLOW", False, True, -.52)])
def test_reward(moved, decision, success, exhausted, expected):
    assert reward_for(moved, 10000, decision, success, exhausted) == pytest.approx(expected)


@pytest.mark.parametrize("target,moved,decision", [(0, 1, "ALLOW"), (1, -1, "ALLOW"),
                                                   (1, float("nan"), "ALLOW"), (1, 0, "BAD")])
def test_reward_rejects(target, moved, decision):
    with pytest.raises(ValueError):
        reward_for(moved, target, decision)


def test_q_update_and_terminal():
    a = QLearningAttacker(alpha=.5, gamma=.9)
    a.row((0, 1, 0))[2] = 4
    a.update((0, 0, 0), 1, 2, (0, 1, 0))
    assert a.row((0, 0, 0))[1] == pytest.approx(2.8)
    a.update((0, 0, 0), 1, 2, (0, 1, 0), terminal=True)
    assert a.row((0, 0, 0))[1] == pytest.approx(2.4)


def test_explore_exploit_and_seed():
    a, b = QLearningAttacker(seed=5, epsilon=1), QLearningAttacker(seed=5, epsilon=1)
    assert [a.select((0, 0, 0)) for _ in range(50)] == [b.select((0, 0, 0)) for _ in range(50)]
    a.epsilon = 0
    a.row((0, 0, 0))[7] = 10
    assert set(a.select((0, 0, 0)) for _ in range(50)) == {7}
    a.epsilon = 1
    assert len(set(a.select((0, 0, 0)) for _ in range(50))) > 5


@pytest.mark.parametrize("state", [(0,), (4, 0, 0), (True, 0, 0), (-1, 0, 0)])
def test_invalid_state(state):
    with pytest.raises(ValueError):
        QLearningAttacker().row(state)


def test_invalid_transition():
    a = QLearningAttacker()
    with pytest.raises(ValueError):
        a.state()
    a.begin_episode(view(), 5)
    with pytest.raises(ValueError):
        a.observe({})
    with pytest.raises(ValueError):
        a.begin_episode(view(), 5)
    a.end_episode("FAILED")
    with pytest.raises(ValueError):
        a.end_episode("FAILED")
    with pytest.raises(ValueError):
        a.update((0, 0, 0), len(ACTIONS), 1, (0, 0, 0))


@pytest.mark.parametrize("index", range(len(ACTIONS)))
def test_all_actions_valid_and_pacing(index):
    cfg = RunConfig(campaigns=1, max_steps=3)
    spec = replace(build_workload(cfg)["known"][0], target_amount=100000)
    a = QLearningAttacker(training=False)
    a.select = lambda state: index
    c = episode(Constant(.1), a, spec, cfg)
    assert len(c.transactions) == 3 and a.updates == 0
    first, second = c.transactions[:2]
    from datetime import datetime
    delta = (datetime.fromisoformat(second["timestamp"]) -
             datetime.fromisoformat(first["timestamp"])).total_seconds()
    assert delta == (180 if ACTIONS[index][1] == "fast" else 900)
    assert all(x["from_vpa"] != x["to_vpa"] and 0 < x["amount"] <= 50000 for x in c.transactions)
    if ACTIONS[index][2] == "reuse":
        assert first["to_vpa"] == second["to_vpa"]
    else:
        assert first["to_vpa"] != second["to_vpa"]


@pytest.mark.parametrize("score,status", [(.1, "SUCCESS"), (.5, "SUCCESS"), (.9, "BLOCKED")])
def test_episode_termination_and_feedback(score, status):
    cfg = RunConfig(campaigns=1, max_steps=30)
    spec = replace(build_workload(cfg)["known"][0], target_amount=1000)
    a = QLearningAttacker()
    c = episode(Constant(score), a, spec, cfg)
    assert c.status.value == status and not a.active
    assert a.updates == 1 and a.last_transition["terminal"]
    assert "risk_score" not in a.history[0] and "features" not in a.history[0]
    assert metrics(c, a)["attempted"] == 1


def test_seeded_episode_and_frozen_policy():
    cfg = RunConfig(seed=77, campaigns=1)
    spec = build_workload(cfg)["known"][0]
    a, b = QLearningAttacker(), QLearningAttacker()
    c, d = episode(Constant(.1), a, spec, cfg), episode(Constant(.1), b, spec, cfg)
    assert c.transactions == d.transactions and a.q == b.q
    before = copy.deepcopy(a.q)
    updates = a.updates
    a.training = False
    episode(Constant(.1), a, spec, cfg)
    assert a.updates == updates
    assert all(a.q[k] == v for k, v in before.items())


def test_save_load_and_incompatible(tmp_path):
    a = QLearningAttacker()
    a.update((0, 0, 0), 3, 1, (0, 0, 1), True)
    path = tmp_path / "q.json"
    a.save(path)
    b = QLearningAttacker.load(path)
    assert b.q == a.q and b.updates == a.updates and not b.training
    with pytest.raises(FileExistsError):
        a.save(path)
    payload = json.loads(path.read_text())
    payload["actions"][0][0] = -1
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(payload))
    with pytest.raises(ValueError):
        QLearningAttacker.load(bad)


def test_learning_changes_real_actions():
    # Safe amounts <=3000; larger proposals are terminally blocked.
    class AmountDetector:
        def predict(self, features):
            return .9 if features["amount"] > 3000 else .1
    cfg = RunConfig(seed=9, campaigns=160, max_steps=8)
    a = QLearningAttacker(epsilon=.2)
    for spec in build_workload(cfg)["known"]:
        episode(AmountDetector(), a, spec, cfg)
    assert a.updates > 160 and any(v != 0 for row in a.q.values() for v in row)
    a.training = False
    spec = replace(build_workload(cfg)["known"][0], target_amount=12000)
    c = episode(AmountDetector(), a, spec, cfg)
    assert c.status.value == "SUCCESS"
    assert max(t["amount"] for t in c.transactions) <= 3000
    assert all(a.q[(0, 3, 0)][i] < max(a.q[(0, 3, 0)])
               for i, action in enumerate(ACTIONS) if action[0] > 3000)


@pytest.mark.parametrize("name", ["xgboost", "random_forest"])
def test_real_detector_integration(name):
    cfg = RunConfig(campaigns=1, max_steps=5)
    c = episode(load_detector(f"models/baseline_{name}.pkl"), QLearningAttacker(),
                build_workload(cfg)["known"][0], cfg)
    assert c.transactions and all(0 <= t["risk_score"] <= 1 for t in c.transactions)


def test_full_comparison_repeatability_and_serialization(tmp_path):
    config = PrototypeConfig(seeds=(11, 12), campaigns=3, episodes=12, max_steps=6)
    a, b = tmp_path / "a", tmp_path / "b"
    result = compare(a, config)
    compare(b, config)
    assert result["campaigns"] == 2 * 2 * 2 * 4 * 3
    assert result["training_episodes"] == 48
    for name in ["campaigns.json", "summary.json", "learning.csv", "transactions.csv", "per_seed.csv"]:
        assert (a / name).read_bytes() == (b / name).read_bytes()
    for manifest in json.loads((a / "manifest.json").read_text())["runs"]:
        assert manifest["evaluation_updates"] == 0
    rows = json.loads((a / "campaigns.json").read_text())
    assert {r["scenario"] for r in rows} == {"S1", "S2", "S3", "S4"}
    assert {r["family"] for r in rows} == {f.value for f in CampaignFamily}
    assert all(r["metrics"]["attempted"] ==
               r["metrics"]["allowed"] + r["metrics"]["flagged"] + r["metrics"]["blocked"] for r in rows)
    assert all(r["metrics"]["proposals"] == r["metrics"]["attempted"] +
               r["metrics"]["rejected_before_execution"] for r in rows)
    assert (a / "comparison.svg").is_file() and (a / "learning.svg").is_file()
    with pytest.raises(FileExistsError):
        compare(a, config)
    loaded = tmp_path / "loaded"
    compare(loaded, config, policy_dir=a)
    assert (a / "campaigns.json").read_bytes() == (loaded / "campaigns.json").read_bytes()
    assert (loaded / "learning.csv").read_bytes() == b""
    with pytest.raises(ValueError, match="mismatch"):
        compare(tmp_path / "mismatch", replace(config, max_steps=7), policy_dir=a)


def test_reject_reserved_output():
    with pytest.raises(ValueError, match="Gate C"):
        compare(Path("/home/user/workspace/gate-c-pilot-01-control/never-create"),
                PrototypeConfig())


@pytest.mark.parametrize("kwargs", [{"seeds": (1, 1)}, {"episodes": 0}, {"campaigns": -1},
                                   {"detector": "other"}, {"attacker": "other"}])
def test_config_rejects(kwargs):
    with pytest.raises(ValueError):
        PrototypeConfig(**kwargs)
