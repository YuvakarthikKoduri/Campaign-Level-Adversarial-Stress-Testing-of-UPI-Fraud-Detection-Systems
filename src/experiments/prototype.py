"""Independent academic experiment API. Does not use semantic_pipeline."""
import csv
from dataclasses import asdict, dataclass
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import statistics

from src.attackers.family_based import make_attacker
from src.attackers.q_learning import QLearningAttacker
from src.campaigns.executor import CampaignExecutor
from src.campaigns.generator import Campaign, CampaignFamily
from src.campaigns.vpa_strategy import VPAStrategy
from src.detectors.baseline import load_detector
from src.environment import UPIEnvironment
from src.environment.thresholds import ThresholdConfig
from src.experiments.config import RunConfig, build_workload, derive_seed

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class PrototypeConfig:
    seeds: tuple = (101, 202, 303)
    campaigns: int = 12
    episodes: int = 300
    max_steps: int = 30
    detector: str = "both"
    attacker: str = "all"
    flag_threshold: float = .4
    block_threshold: float = .7

    def __post_init__(self):
        if (not self.seeds or len(set(self.seeds)) != len(self.seeds)
                or any(type(x) is not int for x in self.seeds)
                or min(self.campaigns, self.episodes, self.max_steps) <= 0):
            raise ValueError("Positive sizes and unique integer seeds required")
        if self.detector not in ("both", "xgboost", "random_forest"):
            raise ValueError("Unknown detector")
        if self.attacker not in ("all", "static", "adaptive", "rl", "untrained_rl"):
            raise ValueError("Unknown attacker")
        ThresholdConfig(self.flag_threshold, self.block_threshold)


def episode(detector, actor, spec, config):
    campaign = Campaign(spec.campaign_id, "prototype-controlled", "synthetic gross transfer",
                        spec.target_amount, spec.fraud_type, CampaignFamily(spec.family),
                        VPAStrategy(spec.vpa_strategy))
    from datetime import datetime
    campaign.created_at = datetime.fromisoformat(spec.start_time)
    campaign.policy_seed, campaign.timer_seed, campaign.vpa_seed = (
        spec.policy_seed, spec.timer_seed, spec.vpa_seed)
    env = UPIEnvironment(ThresholdConfig(config.flag_threshold, config.block_threshold), detector)
    for account in config.accounts:
        env.create_account(account, config.initial_balance)
        env.create_vpa(account, account, account)
    CampaignExecutor(detector, env, actor, config.max_steps, "label_only",
                     config.max_transaction_amount).execute_campaign(campaign, list(config.accounts),
                                                                     seed=config.seed)
    if campaign.status.value == "INVALID":
        raise RuntimeError(f"Invalid episode: {campaign.invalid_action}")
    if not math.isclose(sum(x.balance for x in env.accounts.values()),
                        config.initial_balance * len(config.accounts), abs_tol=1e-6):
        raise RuntimeError("Ledger conservation failed")
    return campaign


def metrics(campaign, actor):
    decisions = [x["decision"] for x in campaign.transactions]
    return dict(success=int(campaign.status.value == "SUCCESS"),
                proposals=campaign.proposals,
                rejected_before_execution=campaign.proposals - len(decisions),
                attempted=len(decisions), allowed=decisions.count("ALLOW"),
                flagged=decisions.count("FLAG"), blocked=decisions.count("BLOCK"),
                exposure=round(campaign.total_amount_moved, 2),
                attempted_amount=round(campaign.total_attempted_amount, 2),
                detection_seconds=campaign.detection_time,
                intervention_seconds=campaign.intervention_time,
                reward=sum(getattr(actor, "rewards", [])) if isinstance(actor, QLearningAttacker) else None,
                termination=campaign.termination_reason)


def dump(path, value):
    with Path(path).open("x") as out:
        json.dump(value, out, sort_keys=True, indent=2, allow_nan=False)


def write_csv(path, rows):
    with Path(path).open("x", newline="") as out:
        if rows:
            writer = csv.DictWriter(out, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


def compare(output, options, policy_dir=None):
    """Train known-family only; freeze Q for paired held-out seed evaluation."""
    output = Path(output).resolve()
    # Prevent accidental use of reserved Gate C locations by this separate CLI.
    reserved = ("gate-c-pilot-01-control", "gate-c-pilot-01-approval-staging", "upi-gc-pilot-01")
    if any(part in reserved for part in output.parts):
        raise ValueError("Gate C paths are not prototype destinations")
    if policy_dir is not None and options.attacker not in ("all", "rl"):
        raise ValueError("Policy directory is meaningful only for RL evaluation")
    output.mkdir(parents=True, exist_ok=False)
    records, learning, manifests = [], [], []
    names = ("xgboost", "random_forest") if options.detector == "both" else (options.detector,)
    policies = ("static", "adaptive", "rl", "untrained_rl") if options.attacker == "all" else (options.attacker,)
    for name in names:
        model = ROOT / "models" / f"baseline_{name}.pkl"
        detector = load_detector(str(model))
        for seed in options.seeds:
            train_seed = derive_seed(seed, "prototype-training")
            config = RunConfig(seed=seed, campaigns=options.campaigns, max_steps=options.max_steps,
                               flag_threshold=options.flag_threshold, block_threshold=options.block_threshold)
            actor = QLearningAttacker(seed=train_seed)
            model_digest = hashlib.sha256(model.read_bytes()).hexdigest()
            if policy_dir is not None:
                actor = QLearningAttacker.load(Path(policy_dir) / f"q_{name}_{seed}.json")
                if (actor.metadata.get("model_sha256") != model_digest
                        or actor.metadata.get("evaluation_seed") != seed
                        or actor.metadata.get("max_steps") != options.max_steps
                        or actor.metadata.get("flag_threshold") != options.flag_threshold
                        or actor.metadata.get("block_threshold") != options.block_threshold):
                    raise ValueError("Checkpoint detector/seed/policy/horizon mismatch")
            elif "rl" in policies:
                train_config = RunConfig(seed=train_seed, campaigns=options.episodes,
                                         max_steps=options.max_steps,
                                         flag_threshold=options.flag_threshold,
                                         block_threshold=options.block_threshold)
                train_workload = build_workload(train_config)["known"]
                for number, spec in enumerate(train_workload):
                    actor.epsilon = max(.05, 1 - .95 * number / max(1, options.episodes - 1))
                    c = episode(detector, actor, spec, train_config)
                    learning.append(dict(detector=name, seed=seed, episode=number + 1,
                                         epsilon=actor.epsilon, updates=actor.updates,
                                         **metrics(c, actor)))
                actor.save(output / f"q_{name}_{seed}.json", metadata=dict(
                    model_sha256=model_digest, detector=name, evaluation_seed=seed,
                    training_seed=train_seed, training_families=["high_value_burst"],
                    max_steps=options.max_steps, flag_threshold=options.flag_threshold,
                    block_threshold=options.block_threshold, training_episodes=options.episodes))
            actor.training, actor.epsilon = False, 0.
            learned_snapshot = {key: list(values) for key, values in actor.q.items()}
            training_updates = actor.updates
            workload = build_workload(config)
            for kind, specs in workload.items():
                for policy in policies:
                    for spec in specs:
                        family = CampaignFamily(spec.family)
                        current = (actor if policy == "rl" else
                                   QLearningAttacker(seed=spec.policy_seed, training=False)
                                   if policy == "untrained_rl" else
                                   make_attacker(family, adaptive=policy == "adaptive", seed=spec.policy_seed))
                        c = episode(detector, current, spec, config)
                        scenario = ("S1" if kind == "known" else "S3") if policy == "static" else (
                            "S2" if kind == "known" else "S4")
                        records.append(dict(detector=name, seed=seed, attacker=policy,
                                            scenario=scenario, kind=kind, family=spec.family,
                                            campaign_id=spec.campaign_id, spec=spec.to_dict(),
                                            metrics=metrics(c, current), outcome=c.to_dict(),
                                            transactions=c.transactions))
            if (actor.updates != training_updates or
                    any(actor.q[key] != values for key, values in learned_snapshot.items())):
                raise RuntimeError("Frozen evaluation changed learned values")
            manifests.append(dict(detector=name, seed=seed, train_seed=train_seed,
                                  training_families=["high_value_burst"],
                                  evaluation_updates=actor.updates - training_updates,
                                  training_updates=actor.updates,
                                  policy_source="checkpoint" if policy_dir is not None else "this_run",
                                  model_sha256=model_digest))
    summaries, per_seed = [], []
    numeric = ("success", "proposals", "rejected_before_execution", "attempted",
               "allowed", "flagged", "blocked", "exposure")
    for name in names:
        for kind in ("known", "unknown"):
            for policy in policies:
                group = [x for x in records if (x["detector"], x["kind"], x["attacker"]) == (name, kind, policy)]
                seed_rows = []
                for seed in options.seeds:
                    selected = [x["metrics"] for x in group if x["seed"] == seed]
                    row = dict(detector=name, kind=kind, attacker=policy, seed=seed, n=len(selected))
                    row.update({key: statistics.mean(x[key] for x in selected) for key in numeric})
                    per_seed.append(row)
                    seed_rows.append(row)
                summary = dict(detector=name, kind=kind, attacker=policy,
                               campaigns=len(group), seeds=len(seed_rows))
                for key in numeric:
                    values = [x[key] for x in seed_rows]
                    summary[key + "_mean"] = statistics.mean(values)
                    summary[key + "_seed_sd"] = statistics.stdev(values) if len(values) > 1 else None
                for timing in ("detection_seconds", "intervention_seconds"):
                    observed = [x["metrics"][timing] for x in group if x["metrics"][timing] is not None]
                    summary[timing + "_observed"] = len(observed)
                    summary[timing + "_mean_observed"] = statistics.mean(observed) if observed else None
                summaries.append(summary)
    dump(output / "config.json", asdict(options))
    dump(output / "campaigns.json", records)
    dump(output / "summary.json", summaries)
    dump(output / "manifest.json", dict(protocol="academic-prototype-v1", runs=manifests,
                                      packages={p: importlib.metadata.version(p) for p in
                                                ("numpy", "pandas", "scikit-learn", "xgboost")},
                                      source_sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                                     for p in [ROOT / "run_prototype.py",
                                                               *sorted((ROOT / "src").rglob("*.py"))]},
                                      dependency_lock_sha256=hashlib.sha256(
                                          (ROOT / "requirements-milestone1.lock").read_bytes()).hexdigest(),
                                      gate_c_workflow=False, scientific_validation=False))
    write_csv(output / "summary.csv", summaries)
    write_csv(output / "per_seed.csv", per_seed)
    write_csv(output / "learning.csv", learning)
    transactions = [dict(detector=r["detector"], seed=r["seed"], attacker=r["attacker"],
                         kind=r["kind"], campaign_id=r["campaign_id"],
                         step=i + 1, amount=t["amount"], timestamp=t["timestamp"],
                         decision=t["decision"], risk_score=t["risk_score"],
                         amount_transferred=t["amount_transferred"])
                    for r in records for i, t in enumerate(r["transactions"])]
    write_csv(output / "transactions.csv", transactions)
    from src.experiments.prototype_plots import plots
    plots(output, summaries, learning)
    return dict(campaigns=len(records), training_episodes=len(learning), summary=summaries)
