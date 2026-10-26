"""Prospective synthetic mechanism pilot; no semantic/Gate C workflow imports.

Fixed exploratory design, not a confirmatory implementation of Protocol v2.
Uses the legacy executor/ledger and Q reward/terminal observer, with explicit
matched legal masks. All artifacts are new; old models and data are untouched.
"""
import argparse
from dataclasses import asdict
from datetime import datetime, timedelta
import hashlib
import json
import math
from pathlib import Path
import pickle
import random
import shutil
import statistics

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from xgboost import XGBClassifier

from src.attackers.q_learning import QLearningAttacker
from src.campaigns.executor import CampaignExecutor
from src.campaigns.generator import Campaign, CampaignFamily
from src.environment import UPIEnvironment
from src.environment.thresholds import ThresholdConfig
from src.experiments.config import derive_seed

FEATURES = ["amount", "hour_of_day", "velocity_1h", "is_new_vpa"]
BANDS = (1000, 3000, 8000, 15000)
ACTIONS = tuple((amount, pace) for amount in BANDS for pace in (300, 1200))
ARMS = ("static", "rule", "rl", "blind_rl", "zero_q")
FAMILIES = ("high_value_burst", "gradual_escalation")
VERSION = "mechanism-pilot-v1"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open("x") as f:
        json.dump(value, f, sort_keys=True, indent=2, allow_nan=False)


def payload_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def has_ge_prefix(events):
    """Nontrivial GE prefix: first band 0, adjacent nondecreasing rise.

    A scalar 1000 alone is not a mechanism signature. Derived GE ancestry is
    excluded separately. All generated nominal bands are checked against amounts.
    """
    if not events or events[0]["band"] != 0:
        return False
    previous, count = 0, 1
    for event in events[1:]:
        band = event["band"]
        if band not in (previous, previous + 1) or (band == previous and count >= 2):
            return False
        if band > previous:
            return True
        count += 1
    return False


def legal_indices(family, previous=-1, repetitions=0):
    if family == FAMILIES[0]:
        bands = (3,) if previous < 0 else (2, 3)
    elif family == FAMILIES[1]:
        if previous < 0:
            bands = (0,)
        elif previous == 3:
            bands = (3,)
        else:
            bands = (previous + 1,) if repetitions >= 2 else (previous, previous + 1)
    else:
        raise ValueError("Unsupported mechanism")
    return [i for i, (amount, _) in enumerate(ACTIONS) if BANDS.index(amount) in bands]


def features(events):
    result = []
    times = [datetime.fromisoformat(e["time"]) for e in events]
    for i, event in enumerate(events):
        recent = sum(0 <= (times[i] - t).total_seconds() < 3600 for t in times[:i])
        result.append([event["paise"] / 100, times[i].hour, recent, int(i == 0)])
    return result


def episode_data(root, role, index, family, label):
    seed = derive_seed(root, role, index)
    rng = random.Random(seed)
    start = datetime(2027, 1, 5) + timedelta(hours=rng.randrange(24))
    target = rng.randint(2000000, 4000000)
    events, moved, previous, repetitions, seconds = [], 0, -1, 0, 0
    length = rng.randint(2, 7) if family == "benign" else 30
    for _ in range(length):
        if family == "benign":
            band = rng.randrange(4)
            pace = rng.choice((300, 1200, 3600))
        else:
            action = rng.choice(legal_indices(family, previous, repetitions))
            amount, pace = ACTIONS[action]
            band = BANDS.index(amount)
        if events:
            seconds += pace
        amount = BANDS[band] * 100
        if family != "benign":
            amount = min(amount, target - moved)
        events.append(dict(paise=amount, time=(start + timedelta(seconds=seconds)).isoformat(),
                           band=band))
        moved += amount
        repetitions = repetitions + 1 if band == previous else 1
        previous = band
        if family != "benign" and moved == target:
            break
    return dict(id=f"{role}-{seed:016x}", role=role, family=family, label=label,
                parent=None, seed=seed, target_paise=target, events=events)


def corpus(root, role, count, benign_only=False, mimic=False):
    episodes, quarantine, attempt = [], [], 0
    while len(episodes) < count:
        if mimic:
            family, label = FAMILIES[1], 0
        elif benign_only or len(episodes) % 2 == 0:
            family, label = "benign", 0
        else:
            family, label = FAMILIES[0], 1
        episode = episode_data(root, role, attempt, family, label)
        attempt += 1
        if not mimic and has_ge_prefix(episode["events"]):
            quarantine.append(episode)
            continue
        episodes.append(episode)
    return episodes, quarantine


def rows(episodes):
    return [dict(episode_id=e["id"], step=i, label=e["label"],
                 **dict(zip(FEATURES, vector)))
            for e in episodes for i, vector in enumerate(features(e["events"]))]


def calibrate(peaks, rate):
    if not peaks or not 0 < rate < 1 or not all(math.isfinite(x) and 0 <= x <= 1 for x in peaks):
        raise ValueError("Invalid benign calibration scores")
    maximum_events = math.floor(rate * len(peaks))
    cutoff = math.nextafter(sorted(peaks)[len(peaks) - maximum_events - 1], math.inf)
    if cutoff > 1:
        raise ValueError("Benign target cannot be calibrated within [0,1]; no all-ALLOW fallback")
    return cutoff


class Detector:
    """In-memory score cache is separate from the immutable fitted artifact."""
    def __init__(self, model):
        self.model, self.cache, self.observations = model, {}, []

    def predict(self, values):
        key = tuple(values[k] for k in FEATURES)
        if key not in self.cache:
            self.cache[key] = float(self.model.predict_proba(
                pd.DataFrame([values], columns=FEATURES))[0, 1])
        self.observations.append(dict(features=dict(values), score=self.cache[key]))
        return self.cache[key]


class MatchedPolicy(QLearningAttacker):
    def __init__(self, mode="rl", seed=42, training=False):
        if mode not in ARMS or (training and mode not in ("rl", "blind_rl")):
            raise ValueError("Invalid matched-policy mode")
        super().__init__(seed=seed, training=training)
        self.mode = mode
        if not training:
            self.epsilon = 0.

    def begin_episode(self, campaign, max_steps):
        super().begin_episode(campaign, max_steps)
        self.family = campaign.family.value
        self.previous, self.repetitions = -1, 0
        self.clock = self.start

    def state(self):
        p, h, d = super().state()
        return p, h, 0 if self.mode in ("static", "blind_rl") else d

    def row(self, state):
        state = tuple(state)
        if len(state) != 3 or any(type(i) is not int or not 0 <= i <= 3 for i in state):
            raise ValueError("Invalid state")
        if not self.training:
            return self.q.get(state, [0.] * len(ACTIONS))
        return self.q.setdefault(state, [0.] * len(ACTIONS))

    def legal(self):
        return legal_indices(self.family, self.previous, self.repetitions)

    def select(self, state):
        legal = self.legal()
        if self.mode in ("static", "rule"):
            decision = self.last_decision if self.mode == "rule" else "NEUTRAL"
            amount = min(ACTIONS[i][0] for i in legal) if decision == "FLAG" else max(ACTIONS[i][0] for i in legal)
            pace = 300 if decision == "ALLOW" else 1200
            return next(i for i in legal if ACTIONS[i] == (amount, pace))
        if self.training and self.random.random() < self.epsilon:
            return self.random.choice(legal)
        values = self.row(state)
        best = max(values[i] for i in legal)
        return self.random.choice([i for i in legal if values[i] == best])

    def update(self, state, action, reward, next_state, terminal=False):
        if not self.training:
            raise ValueError("Frozen policy cannot update")
        if type(action) is not int or not 0 <= action < len(ACTIONS) or not math.isfinite(reward):
            raise ValueError("Invalid TD update")
        row = self.row(state)
        future = 0 if terminal else max(self.row(next_state)[i] for i in self.legal())
        row[action] += self.alpha * (reward + self.gamma * future - row[action])
        self.updates += 1

    def choose_action(self, campaign, state, accounts):
        if not self.active or self.pending is not None or self.terminal_seen or self.step >= self.max_steps:
            raise ValueError("Invalid action lifecycle")
        observation, mask = self.state(), self.legal()
        action = self.select(observation)
        if action not in mask:
            raise ValueError("Illegal action selected")
        nominal, pace = ACTIONS[action]
        amount_paise = min(nominal * 100, round(self.target * 100) - round(self.moved * 100))
        if self.step:
            self.clock += timedelta(seconds=pace)
        band = BANDS.index(nominal)
        self.repetitions = self.repetitions + 1 if self.previous == band else 1
        self.previous = band
        self.step += 1
        self.pending, self.current_mask, self.current_action = (observation, action), mask, action
        self.action_history.append(action)
        return dict(from_vpa=accounts[0], to_vpa=accounts[1], amount=amount_paise / 100,
                    timestamp=self.clock.isoformat(), campaign_id=campaign.campaign_id, step=self.step)

    def observe(self, response):
        super().observe(response)
        self.last_transition.update(action_parameters=list(ACTIONS[self.current_action]),
                                    legal_mask=self.current_mask,
                                    next_legal_mask=[] if self.terminal_seen else self.legal())

    def policy_payload(self, metadata=None):
        result = super().policy_payload(metadata)
        result.update(version=VERSION, mode=self.mode, actions=[list(a) for a in ACTIONS])
        return result

    @classmethod
    def restore(cls, path, metadata):
        p = json.loads(Path(path).read_text())
        required = {"version", "mode", "actions", "alpha", "gamma", "epsilon",
                    "updates", "metadata", "q"}
        if (not isinstance(p, dict) or set(p) != required or p.get("version") != VERSION
                or p.get("actions") != [list(a) for a in ACTIONS]
                or payload_hash(p.get("metadata")) != payload_hash(metadata)
                or p.get("mode") != metadata["mode"] or not isinstance(p.get("q"), dict)):
            raise ValueError("Checkpoint schema/lineage mismatch")
        actor = cls(p["mode"])
        if (any(type(p[k]) not in (int, float) or not math.isfinite(p[k])
                for k in ("alpha", "gamma", "epsilon"))
                or not (0 < p["alpha"] <= 1 and 0 <= p["gamma"] <= 1 and 0 <= p["epsilon"] <= 1)):
            raise ValueError("Invalid checkpoint hyperparameters")
        if type(p["updates"]) is not int or p["updates"] < 0:
            raise ValueError("Invalid checkpoint update count")
        actor.alpha, actor.gamma, actor.epsilon = p["alpha"], p["gamma"], p["epsilon"]
        actor.updates, actor.metadata = p["updates"], p["metadata"]
        for key, values in p["q"].items():
            state = tuple(map(int, key.split(",")))
            actor.row(state)
            if len(values) != len(ACTIONS) or not all(type(v) in (int, float) and math.isfinite(v) for v in values):
                raise ValueError("Invalid checkpoint Q values")
            actor.q[state] = list(values)
        return actor


def execute(detector, policy, context, thresholds):
    campaign = Campaign(context["id"], "matched pilot", "synthetic gross source debit",
                        context["target_paise"] / 100, "synthetic", CampaignFamily(context["family"]))
    campaign.created_at = datetime.fromisoformat(context["start"])
    campaign.budget, campaign.max_duration_seconds = campaign.target_amount, 86400
    campaign.policy_seed = derive_seed(context["seed"], "policy")
    policy.start = campaign.created_at
    env = UPIEnvironment(ThresholdConfig(*thresholds), detector)
    accounts = ("source@synthetic", "sink@synthetic")
    for account in accounts:
        env.create_account(account, 500000)
        env.create_vpa(account, account, account)
    offset = len(detector.observations)
    CampaignExecutor(detector, env, policy, 30, "label_only", 15000).execute_campaign(
        campaign, list(accounts), seed=context["seed"])
    observed = detector.observations[offset:]
    assert len(observed) == len(campaign.transactions)
    for tx, feature in zip(campaign.transactions, observed):
        tx["computed_features"] = feature["features"]
    assert round((500000 - env.accounts[accounts[0]].balance) * 100) == round(campaign.total_amount_moved * 100)
    assert round(sum(a.balance for a in env.accounts.values()) * 100) == 100000000
    return dict(context=context, status=campaign.status.value, reason=campaign.termination_reason,
                success=int(campaign.status.value == "SUCCESS"), proposals=campaign.proposals,
                gross_paise=round(campaign.total_amount_moved * 100),
                transactions=campaign.transactions)


def contexts(root, count, family):
    result = []
    for i in range(count):
        seed = derive_seed(root, "evaluation", family, i)
        rng = random.Random(seed)
        result.append(dict(id=f"eval-{family}-{seed:016x}", seed=seed, family=family,
                           target_paise=rng.randint(2000000, 4000000),
                           start=(datetime(2027, 2, 1) + timedelta(hours=rng.randrange(24))).isoformat()))
    return result


def episode_peaks(model, episodes):
    vectors = [x for e in episodes for x in features(e["events"])]
    scores = model.predict_proba(pd.DataFrame(vectors, columns=FEATURES))[:, 1]
    cursor, result = 0, []
    for episode in episodes:
        n = len(episode["events"])
        sequence = list(map(float, scores[cursor:cursor+n]))
        cursor += n
        result.append(dict(id=episode["id"], family=episode["family"],
                           label=episode["label"], scores=sequence, peak=max(sequence)))
    return result


def run(options):
    output = Path(options.output)
    output.mkdir(parents=True, exist_ok=False)
    config = {k: v for k, v in vars(options).items() if k not in ("output", "reload_from")}
    write(output / "config.json", config)
    project = Path(__file__).parents[2]
    code = {str(p.relative_to(project)): digest(p) for p in [
        *sorted((project/"src").rglob("*.py")), project/"requirements-milestone1.lock",
        project/"docs/MECHANISM_PILOT_DESIGN.md"]}
    write(output / "source.json", code)
    if options.reload_from:
        reference = Path(options.reload_from)
        if json.loads((reference / "config.json").read_text()) != config:
            raise ValueError("Reload configuration mismatch")
        if json.loads((reference / "source.json").read_text()) != code:
            raise ValueError("Reload source mismatch")
    all_records, inventory = [], []
    training_total = 0
    for block in range(options.blocks):
        root = derive_seed(options.seed_base, "independent-block", block)
        folder = output / f"block-{block:02d}"
        folder.mkdir()
        datasets, quarantines = {}, {}
        for role, count, kwargs in [
            ("train", options.train_episodes, {}),
            ("validation", options.validation, {}),
            ("calibration", options.calibration, {"benign_only": True}),
            ("benign_test", options.benign_test, {"benign_only": True}),
            ("benign_mimic_test", options.benign_test, {"mimic": True}),
        ]:
            datasets[role], quarantines[role] = corpus(root, role, count, **kwargs)
        ids = [e["id"] for group in datasets.values() for e in group]
        assert len(ids) == len(set(ids))
        for role in ("train", "validation", "calibration"):
            assert not any(e["family"] == FAMILIES[1] or has_ge_prefix(e["events"])
                           for e in datasets[role])
        write(folder / "episodes.json", datasets)
        write(folder / "quarantined.json", quarantines)
        train_rows, validation_rows = rows(datasets["train"]), rows(datasets["validation"])
        pd.DataFrame(train_rows).to_csv(folder / "fit_rows.csv", index=False)
        pd.DataFrame(validation_rows).to_csv(folder / "validation_rows.csv", index=False)
        plan = [c for family in FAMILIES for c in contexts(root, options.contexts, family)]
        write(folder / "evaluation_plan.json", plan)
        X = pd.DataFrame(train_rows)[FEATURES]
        y = np.array([r["label"] for r in train_rows])
        for algorithm in ("xgboost", "random_forest"):
            path = folder / algorithm
            path.mkdir()
            fitting_seed = derive_seed(root, "detector-fit", algorithm) % (2**32)
            if options.reload_from:
                prior = Path(options.reload_from) / folder.name / algorithm
                previous_binding = json.loads((prior / "fit_binding.json").read_text())
                for filename in ("episodes.json", "fit_rows.csv", "validation_rows.csv", "evaluation_plan.json"):
                    assert digest(folder / filename) == digest(prior.parent / filename)
                assert digest(prior / "model.pkl") == previous_binding["model_sha256"]
                shutil.copyfile(prior / "model.pkl", path / "model.pkl")
                model = pickle.loads((path / "model.pkl").read_bytes())
            else:
                model = (XGBClassifier(n_estimators=100, max_depth=4, learning_rate=.1,
                    subsample=1, colsample_bytree=1, n_jobs=1, random_state=fitting_seed,
                    eval_metric="logloss") if algorithm == "xgboost" else
                    RandomForestClassifier(n_estimators=150, max_depth=8, n_jobs=1,
                                           random_state=fitting_seed))
                model.fit(X, y)
                with (path / "model.pkl").open("xb") as f:
                    pickle.dump(model, f)
            model_sha = digest(path / "model.pkl")
            binding = dict(protocol=VERSION, algorithm=algorithm, model_sha256=model_sha,
                fitting_seed=fitting_seed, fit_rows_sha256=digest(folder / "fit_rows.csv"),
                episode_registry_sha256=digest(folder / "episodes.json"),
                feature_order=FEATURES, parameters={
                    k: ("NaN" if isinstance(v, float) and math.isnan(v) else v)
                    for k, v in model.get_params().items()},
                fit_episode_ids=[e["id"] for e in datasets["train"]],
                forbidden_fit_mechanisms=[], allowed_fraud_families=[FAMILIES[0]],
                fitting_rows=len(X), fitting_label_sha256=payload_hash(y.tolist()),
                feature_matrix_sha256=payload_hash(X.values.tolist()),
                validation_auc=float(roc_auc_score([r["label"] for r in validation_rows],
                    model.predict_proba(pd.DataFrame(validation_rows)[FEATURES])[:, 1])),
                source_sha256=code)
            if options.reload_from:
                assert binding == previous_binding
            write(path / "fit_binding.json", binding)
            calibration = episode_peaks(model, datasets["calibration"])
            flag = calibrate([r["peak"] for r in calibration], .025)
            block_threshold = calibrate([r["peak"] for r in calibration], .005)
            if flag >= block_threshold:
                block_threshold = math.nextafter(flag, math.inf)
            if not 0 <= flag < block_threshold <= 1:
                raise ValueError("Calibration ordering/range failure")
            thresholds = flag, block_threshold
            benign = {role: episode_peaks(model, datasets[role])
                      for role in ("benign_test", "benign_mimic_test")}
            write(path / "benign_scores.json", benign)
            write(path / "calibration.json", dict(flag=flag, block=block_threshold,
                target_any_alert=.025, target_any_block=.005, episodes=calibration,
                achieved_any_alert=statistics.mean(r["peak"] >= flag for r in calibration),
                achieved_any_block=statistics.mean(r["peak"] >= block_threshold for r in calibration),
                method="nextafter above conservative empirical episode-maximum order statistic"))
            detector, policies = Detector(model), {}
            model_payload_before = hashlib.sha256(pickle.dumps(model)).hexdigest()
            with (path / "training.jsonl").open("x") as stream:
                for arm in ("rl", "blind_rl"):
                    policy_seed = derive_seed(root, "rl-policy", algorithm)
                    metadata = dict(mode=arm, model_sha256=model_sha, root=root,
                        training_seed=policy_seed, families=[FAMILIES[0]], episodes=options.episodes,
                        schema=VERSION, source_sha256=code,
                        training_context_ids=[
                            contexts(derive_seed(root, "rl-training", i), 1, FAMILIES[0])[0]["id"].replace("eval-", "rltrain-")
                            for i in range(options.episodes)])
                    if options.reload_from:
                        prior = Path(options.reload_from) / folder.name / algorithm
                        policy = MatchedPolicy.restore(prior / f"{arm}.json", metadata)
                    else:
                        policy = MatchedPolicy(arm, policy_seed, training=True)
                        policy.metadata = metadata
                        for index in range(options.episodes):
                            context = contexts(derive_seed(root, "rl-training", index), 1, FAMILIES[0])[0]
                            context["id"] = context["id"].replace("eval-", "rltrain-")
                            policy.epsilon = max(.05, 1 - .95 * index / max(1, options.episodes-1))
                            record = execute(detector, policy, context, thresholds)
                            record.update(index=index, arm=arm, block=block, detector=algorithm)
                            stream.write(json.dumps(record, sort_keys=True, allow_nan=False) + "\n")
                            training_total += 1
                    policy.training, policy.epsilon = False, 0.
                    policy.save(path / f"{arm}.json")
                    policies[arm] = policy
            frozen, records = [], []
            for arm in ARMS:
                policy = policies.get(arm) or MatchedPolicy(arm)
                before = policy.policy_payload()
                for context in plan:
                    record = execute(detector, policy, context, thresholds)
                    record.update(arm=arm, detector=algorithm, block=block)
                    records.append(record)
                    assert before == policy.policy_payload()
                frozen.append(dict(arm=arm, before=payload_hash(before),
                    after=payload_hash(policy.policy_payload()), updates_before=before["updates"],
                    updates_after=policy.updates, episodes=len(plan)))
            with (path / "campaigns.jsonl").open("x") as stream:
                for r in records:
                    stream.write(json.dumps(r, sort_keys=True, allow_nan=False) + "\n")
            write(path / "frozen_evaluation.json", frozen)
            model_payload_after = hashlib.sha256(pickle.dumps(model)).hexdigest()
            assert model_payload_before == model_payload_after, "Inference changed persisted model state"
            assert digest(path / "model.pkl") == model_sha, "Model artifact changed during evaluation"
            all_records.extend(records)
            inventory.append(dict(block=block, detector=algorithm, model_sha256=model_sha,
                model_payload_before=model_payload_before, model_payload_after=model_payload_after,
                flag=flag, block_threshold=block_threshold, validation_auc=binding["validation_auc"],
                calibration_block_rate=statistics.mean(e["peak"] >= block_threshold for e in calibration),
                ordinary_block_rate=statistics.mean(e["peak"] >= block_threshold for e in benign["benign_test"]),
                mimic_block_rate=statistics.mean(e["peak"] >= block_threshold for e in benign["benign_mimic_test"])))
            print(f"block={block} detector={algorithm} campaigns={len(records)}", flush=True)
    summaries = []
    for algorithm in ("xgboost", "random_forest"):
        for family in FAMILIES:
            for arm in ARMS:
                selected = [r for r in all_records if r["detector"] == algorithm
                            and r["context"]["family"] == family and r["arm"] == arm]
                means = [statistics.mean(r["success"] for r in selected if r["block"] == b)
                         for b in range(options.blocks)]
                summaries.append(dict(detector=algorithm, family=family, arm=arm,
                    n=len(selected), success=statistics.mean(means),
                    seed_sd=statistics.stdev(means) if len(means) > 1 else None,
                    gross_mean=statistics.mean(r["gross_paise"]/100 for r in selected),
                    attempts_mean=statistics.mean(len(r["transactions"]) for r in selected)))
    write(output / "summary.json", summaries)
    pd.DataFrame(summaries).to_csv(output / "summary.csv", index=False)
    write(output / "manifest.json", dict(protocol=VERSION, exploratory=True,
        confirmatory=False, gate_c=False, training_episodes_executed=training_total,
        evaluation_campaigns=len(all_records), blocks=inventory, config=config,
        mode="reload" if options.reload_from else "fit", source_sha256=code))
    print(json.dumps(dict(training=training_total, evaluation=len(all_records))))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", required=True)
    p.add_argument("--reload-from")
    p.add_argument("--blocks", type=int, default=9)
    p.add_argument("--episodes", type=int, default=300)
    p.add_argument("--contexts", type=int, default=40)
    p.add_argument("--train-episodes", type=int, default=1000)
    p.add_argument("--validation", type=int, default=400)
    p.add_argument("--calibration", type=int, default=1000)
    p.add_argument("--benign-test", type=int, default=400)
    p.add_argument("--seed-base", type=int, default=41000)
    args = p.parse_args()
    if min(args.blocks, args.episodes, args.contexts, args.train_episodes,
           args.validation, args.calibration, args.benign_test) <= 0 or args.train_episodes < 4:
        p.error("Positive sizes and at least four detector-fit episodes required")
    run(args)


if __name__ == "__main__":
    main()
