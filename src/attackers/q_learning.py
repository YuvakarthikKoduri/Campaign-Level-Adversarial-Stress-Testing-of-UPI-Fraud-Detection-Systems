"""Tabular attacker for the legacy simulator; never imports Gate C workflows."""
from datetime import timedelta
import itertools
import json
import math
from pathlib import Path
import random
from src.money import add_money, subtract_money, at_least


# Supported simulator controls: amount, family-bounded pacing, recipient choice.
ACTIONS = tuple(itertools.product((1000, 3000, 8000, 15000), ("fast", "slow"),
                                  ("reuse", "rotate")))
VERSION = "prototype-tabular-q-v1"


def reward_for(moved, target, decision, success=False, exhausted=False):
    """Progress + completion, minus blocking, flags, effort and failed horizon."""
    if (not math.isfinite(moved) or not math.isfinite(target) or target <= 0
            or moved < 0 or decision not in ("ALLOW", "FLAG", "BLOCK")):
        raise ValueError("Invalid public reward inputs")
    return (3 * min(moved / target, 1) + 2 * bool(success)
            - 1 * (decision == "BLOCK") - .2 * (decision == "FLAG")
            - .02 - .5 * bool(exhausted and not success and decision != "BLOCK"))


class QLearningAttacker:
    """Learns only from its own accepted feedback; no detector internals or labels."""

    def __init__(self, seed=42, alpha=.25, gamma=.95, epsilon=.1, training=True):
        if not (0 < alpha <= 1 and 0 <= gamma <= 1 and 0 <= epsilon <= 1):
            raise ValueError("Invalid learning parameters")
        self.alpha, self.gamma, self.epsilon = alpha, gamma, epsilon
        self.training, self.random = training, random.Random(seed)
        self.q = {}
        self.metadata = {}
        self.updates = 0
        self.active = False
        self.timer = self.vpa_selector = None

    def begin_episode(self, campaign, max_steps):
        if self.active or max_steps <= 0 or campaign.target_amount <= 0:
            raise ValueError("Invalid episode start")
        self.target, self.max_steps = campaign.target_amount, max_steps
        self.step, self.moved, self.last_decision = 0, 0., "START"
        self.history, self.rewards, self.action_history = [], [], []
        self.pending = None
        self.last_transition = None
        self.last_beneficiary = None
        self.terminal_seen = False
        self.active = True

    def state(self):
        if not self.active:
            raise ValueError("No active episode")
        progress = min(3, int(4 * self.moved / self.target))
        remaining = min(3, int(4 * (self.max_steps - self.step) / self.max_steps))
        decision = {"START": 0, "ALLOW": 1, "FLAG": 2, "BLOCK": 3}[self.last_decision]
        # Own history only; no test labels, detector features or ledger access.
        return progress, remaining, decision

    def row(self, state):
        state = tuple(state)
        if len(state) != 3 or any(type(x) is not int or not 0 <= x <= 3 for x in state):
            raise ValueError("Invalid discrete state")
        if not self.training:
            return self.q.get(state, [0.] * len(ACTIONS))
        return self.q.setdefault(state, [0.] * len(ACTIONS))

    def select(self, state):
        values = self.row(state)
        if self.training and self.random.random() < self.epsilon:
            return self.random.randrange(len(ACTIONS))
        best = max(values)
        return self.random.choice([i for i, value in enumerate(values) if value == best])

    def update(self, state, action, reward, next_state, terminal=False):
        if not self.training:
            raise ValueError("Cannot update a frozen evaluation policy")
        if (type(action) is not int or not 0 <= action < len(ACTIONS)
                or not math.isfinite(reward)):
            raise ValueError("Invalid learning transition")
        row = self.row(state)
        future = 0 if terminal else max(self.row(next_state))
        row[action] += self.alpha * (reward + self.gamma * future - row[action])
        self.updates += 1

    def choose_action(self, campaign, state, accounts):
        if (not self.active or self.pending is not None or self.step >= self.max_steps
                or self.terminal_seen):
            raise ValueError("Invalid action transition")
        observation = self.state()
        index = self.select(observation)
        amount, pace, recipient_mode = ACTIONS[index]
        amount = round(min(amount, max(.01, subtract_money(self.target, self.moved))), 2)
        source = (self.vpa_selector.select_source_vpa() if self.vpa_selector
                  else self.random.choice(accounts))
        available = [x for x in accounts if x != source]
        if not available:
            raise ValueError("Distinct recipient required")
        fresh = [x for x in available if x != self.last_beneficiary]
        recipient = (self.last_beneficiary if recipient_mode == "reuse"
                     and self.last_beneficiary in available else
                     self.random.choice(fresh or available))
        if self.timer is None:
            raise ValueError("Family timer required")
        previous = self.timer.current_time
        when = self.timer.next_transaction_time()
        if self.step:
            model = self.timer.timing_model
            interval = (model.min_interval_seconds if pace == "fast"
                        else model.max_interval_seconds)
            when = previous + timedelta(seconds=interval)
            self.timer.current_time = when
        self.step += 1
        self.pending = observation, index
        self.last_beneficiary = recipient
        self.action_history.append(index)
        return dict(from_vpa=source, to_vpa=recipient, amount=amount,
                    timestamp=when.isoformat(), campaign_id=campaign.campaign_id,
                    step=self.step)

    def observe(self, response):
        if not self.active or self.pending is None:
            raise ValueError("Feedback without pending action")
        decision = response.get("decision")
        transferred = response.get("amount_transferred")
        if (decision not in ("ALLOW", "FLAG", "BLOCK") or not isinstance(transferred, (int, float))
                or not math.isfinite(transferred) or transferred < 0):
            raise ValueError("Invalid feedback")
        state, action = self.pending
        self.moved = add_money(self.moved, transferred)
        self.last_decision = decision
        success = at_least(self.moved, self.target)
        terminal = success or decision == "BLOCK" or self.step == self.max_steps
        reward = reward_for(transferred, self.target, decision, success,
                            self.step == self.max_steps)
        if self.training:
            self.update(state, action, reward, self.state(), terminal)
        self.last_transition = dict(state=list(state), action=action,
                                    action_parameters=list(ACTIONS[action]),
                                    reward=reward, next_state=list(self.state()),
                                    terminal=terminal, training=self.training)
        self.history.append(dict(response))
        self.rewards.append(reward)
        self.pending = None
        self.terminal_seen = terminal

    def end_episode(self, status):
        if not self.active:
            raise ValueError("Episode already ended")
        if self.pending is not None:
            # Invalid/budget/time rejection before an environment response.
            state, action = self.pending
            penalty = -1.02
            if self.training:
                self.update(state, action, penalty, state, terminal=True)
            self.rewards.append(penalty)
            self.pending = None
        self.active = False

    def policy_payload(self, metadata=None):
        """Complete persisted policy; excludes per-episode history and RNG stream."""
        return dict(version=VERSION, actions=[list(x) for x in ACTIONS],
                       alpha=self.alpha, gamma=self.gamma, epsilon=self.epsilon,
                       updates=self.updates, metadata=self.metadata if metadata is None else metadata,
                       q={",".join(map(str, k)): v for k, v in sorted(self.q.items())})

    def save(self, path, metadata=None):
        with Path(path).open("x") as stream:
            json.dump(self.policy_payload(metadata), stream, sort_keys=True, indent=2, allow_nan=False)

    @classmethod
    def load(cls, path, seed=42, training=False):
        payload = json.loads(Path(path).read_text())
        required = {"version", "actions", "alpha", "gamma", "epsilon", "updates", "metadata", "q"}
        if not isinstance(payload, dict) or set(payload) != required:
            raise ValueError("Malformed policy schema: required fields do not match")
        if payload["version"] != VERSION or payload["actions"] != [list(x) for x in ACTIONS]:
            raise ValueError("Incompatible policy")
        if any(type(payload[k]) not in (int, float) or not math.isfinite(payload[k])
               for k in ("alpha", "gamma", "epsilon")):
            raise ValueError("Malformed policy learning parameters")
        actor = cls(seed, payload["alpha"], payload["gamma"], payload["epsilon"], training)
        actor.metadata = payload.get("metadata", {})
        if not isinstance(actor.metadata, dict) or not isinstance(payload["q"], dict):
            raise ValueError("Malformed policy metadata or Q table")
        for key, values in payload["q"].items():
            try:
                state = tuple(map(int, key.split(",")))
            except (AttributeError, ValueError) as exc:
                raise ValueError("Malformed Q state key") from exc
            actor.row(state)
            if (not isinstance(values, list) or len(values) != len(ACTIONS)
                    or any(type(x) not in (int, float) or not math.isfinite(x) for x in values)):
                raise ValueError("Invalid Q values")
            actor.q[state] = list(values)
        if type(payload["updates"]) is not int or payload["updates"] < 0:
            raise ValueError("Invalid update count")
        actor.updates = payload["updates"]
        return actor
