"""Independent assertions for the additive exploratory harness."""
from copy import deepcopy
from datetime import datetime
import json
import math
from types import SimpleNamespace

import pytest

from src.campaigns.generator import CampaignFamily
from src.experiments.mechanism_pilot import (
    ACTIONS, ARMS, BANDS, FAMILIES, Detector, MatchedPolicy, calibrate,
    contexts, corpus, execute, features, has_ge_prefix, legal_indices, rows,
)


class Constant:
    def __init__(self, score):
        self.score = score

    def predict_proba(self, frame):
        import numpy as np
        return np.array([[1-self.score, self.score] for _ in range(len(frame))])


def begin(mode="rl", training=False, family=FAMILIES[0], target=23460.31):
    p = MatchedPolicy(mode, 19, training)
    p.start = datetime(2027, 1, 1)
    p.begin_episode(SimpleNamespace(target_amount=target, family=CampaignFamily(family)), 30)
    return p


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("previous,repetitions", [(-1, 0), (0, 1), (0, 2), (1, 1), (2, 2), (3, 4)])
def test_masks_nonempty_and_same_for_all_arms(family, previous, repetitions):
    masks = []
    for mode in ARMS:
        p = begin(mode, family=family)
        p.previous, p.repetitions = previous, repetitions
        masks.append(p.legal())
    assert masks and all(m == masks[0] for m in masks)
    assert all(0 <= a < 8 for a in masks[0])


def test_hvb_and_escalation_rules():
    assert {ACTIONS[i][0] for i in legal_indices(FAMILIES[0])} == {15000}
    assert {ACTIONS[i][0] for i in legal_indices(FAMILIES[0], 3, 1)} == {8000, 15000}
    assert {ACTIONS[i][0] for i in legal_indices(FAMILIES[1])} == {1000}
    assert {ACTIONS[i][0] for i in legal_indices(FAMILIES[1], 0, 2)} == {3000}
    with pytest.raises(ValueError):
        legal_indices("made-up")


@pytest.mark.parametrize("mode", ARMS)
def test_exact_completion_no_extra_cent_and_no_postterminal(mode):
    p = begin(mode)
    p.select = lambda _: 6  # 15000 at fast pace; second action clipped
    campaign = SimpleNamespace(campaign_id="test")
    amounts = []
    for _ in range(2):
        action = p.choose_action(campaign, {}, ["s", "t"])
        amounts.append(action["amount"])
        p.observe(dict(decision="ALLOW", amount_transferred=action["amount"]))
    assert amounts == [15000, 8460.31]
    assert p.moved == 23460.31 and p.terminal_seen
    assert p.rewards[0] == pytest.approx(3 * 15000 / 23460.31 - .02)
    assert p.rewards[1] == pytest.approx(3 * 8460.31 / 23460.31 + 2 - .02)
    assert sum(r - 3*a/23460.31 + .02 for r, a in zip(p.rewards, amounts)) == pytest.approx(2)
    with pytest.raises(ValueError):
        p.choose_action(campaign, {}, ["s", "t"])
    assert len(p.rewards) == 2


def test_masked_bootstrap_and_terminal_update():
    p = begin(training=True)
    state, after = (0, 3, 0), (1, 2, 1)
    p.previous, p.repetitions = 3, 1
    p.q[after] = [1e6] * 4 + [2., 2., 2., 2.]
    p.update(state, 6, 1., after)
    assert p.q[state][6] == pytest.approx(.25 * (1 + .95 * 2))
    p.q[state][6] = 0
    p.update(state, 6, 1., after, terminal=True)
    assert p.q[state][6] == .25


@pytest.mark.parametrize("mode", ARMS)
def test_frozen_full_payload_unseen_states_and_complete_episode(mode):
    p = MatchedPolicy(mode)
    before = deepcopy(p.policy_payload())
    p.row((3, 3, 3))
    c = contexts(99, 1, FAMILIES[1])[0]
    record = execute(Detector(Constant(.1)), p, c, (.4, .7))
    assert record["success"] == 1
    assert p.policy_payload() == before
    assert p.updates == 0
    assert not p.q
    assert all(not t["rl_transition"]["terminal"] for t in record["transactions"][:-1])


@pytest.mark.parametrize("mode", ARMS)
def test_real_block_terminates_every_arm(mode):
    r = execute(Detector(Constant(.9)), MatchedPolicy(mode), contexts(9, 1, FAMILIES[0])[0], (.4, .7))
    assert not r["success"] and len(r["transactions"]) == 1
    assert r["gross_paise"] == 0 and r["transactions"][0]["rl_transition"]["terminal"]


def test_rule_and_static_use_same_kernel_only_label_differs():
    a, b = begin("static"), begin("rule")
    a.last_decision = b.last_decision = "ALLOW"
    assert ACTIONS[a.select(a.state())] == (15000, 1200)
    assert ACTIONS[b.select(b.state())] == (15000, 300)
    b.last_decision = "START"
    assert a.select(a.state()) == b.select(b.state())


def test_blind_state_cannot_read_label():
    p = begin("blind_rl")
    p.last_decision = "FLAG"
    first = p.state()
    p.last_decision = "ALLOW"
    assert first == p.state()


def test_feature_boundaries_are_causal():
    e = [dict(paise=100000, time="2027-01-01T00:00:00"),
         dict(paise=300000, time="2027-01-01T00:59:59"),
         dict(paise=800000, time="2027-01-01T01:00:00")]
    assert features(e) == [[1000, 0, 0, 1], [3000, 0, 1, 0], [8000, 1, 1, 0]]


def test_training_split_and_mechanism_provenance():
    ids = set()
    for role in ("train", "validation", "calibration"):
        data, quarantine = corpus(91, role, 100, benign_only=role == "calibration")
        assert not any(e["family"] == FAMILIES[1] or has_ge_prefix(e["events"]) for e in data)
        assert not ids.intersection(e["id"] for e in data)
        ids.update(e["id"] for e in data)
        assert all(e["parent"] is None for e in data)
        assert all(e["label"] == 0 for e in data) if role == "calibration" else {e["label"] for e in data} == {0, 1}
        assert set(rows(data)[0]) == {"episode_id", "step", "label", "amount", "hour_of_day", "velocity_1h", "is_new_vpa"}


@pytest.mark.parametrize("rate", [.005, .025])
def test_calibration_ties_conservative(rate):
    values = [0.1] * 990 + [0.5] * 10
    cutoff = calibrate(values, rate)
    assert sum(s >= cutoff for s in values) / 1000 <= rate


@pytest.mark.parametrize("values", [[], [math.nan], [math.inf], [1.], [-.1]])
def test_invalid_or_impossible_calibration_rejected(values):
    with pytest.raises(ValueError):
        calibrate(values, .005)


def test_policy_reload_and_metadata_rejection(tmp_path):
    p = begin(training=True)
    p.metadata = dict(mode="rl", model="digest", training_seed=12)
    p.q[(0, 3, 0)] = [1.] * 8
    p.training, p.epsilon = False, 0
    f = tmp_path / "policy.json"
    p.save(f)
    q = MatchedPolicy.restore(f, p.metadata)
    assert p.policy_payload() == q.policy_payload()
    with pytest.raises(ValueError, match="lineage"):
        MatchedPolicy.restore(f, dict(mode="rl", model="wrong", training_seed=12))
    raw = json.loads(f.read_text())
    raw["alpha"] = True
    f.write_text(json.dumps(raw))
    with pytest.raises(ValueError, match="hyperparameters"):
        MatchedPolicy.restore(f, p.metadata)
