"""Check byte equality AND evidence coverage, never scientific validity."""
import argparse
import csv
import hashlib
import json
import math
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
COMMON = ["campaigns.json", "summary.json", "summary.csv", "per_seed.csv",
          "transactions.csv", "comparison.svg"]
REPEATED = COMMON + ["learning.csv", "learning.svg", "manifest.json"]
METRICS = ("success", "proposals", "rejected_before_execution", "attempted",
           "allowed", "flagged", "blocked", "exposure")
SUMMARY_NUMERIC = {f"{key}_{suffix}" for key in METRICS for suffix in ("mean", "seed_sd")}
TIMINGS = ("detection_seconds", "intervention_seconds")
SUMMARY_FIELDS = (SUMMARY_NUMERIC | {"campaigns", "seeds"} |
                  {f"{key}_{suffix}" for key in TIMINGS
                   for suffix in ("observed", "mean_observed")})


def number(value, field, low=0, high=None):
    """JSON numbers exclude booleans; all emitted metrics must be finite."""
    require(type(value) in (int, float) and math.isfinite(value),
            f"{field}: expected a finite numeric value")
    require((low is None or value >= low) and (high is None or value <= high),
            f"{field}: outside range [{low}, {high}]")
    return value


def metric_means(values, steps, field):
    for key in METRICS:
        number(values.get(key), f"{field}.{key}", high=(
            1 if key == "success" else None if key == "exposure" else steps))
    require(math.isclose(values["allowed"] + values["flagged"] + values["blocked"],
                         values["attempted"], rel_tol=1e-9, abs_tol=1e-9),
            f"{field}: decision counts do not sum to attempted")
    require(math.isclose(values["attempted"] + values["rejected_before_execution"],
                         values["proposals"], rel_tol=1e-9, abs_tol=1e-9),
            f"{field}: proposal counts are inconsistent")


def specification(spec, row):
    fields = {"campaign_id", "family", "fraud_type", "target_amount", "vpa_strategy",
              "start_time", "policy_seed", "timer_seed", "vpa_seed", "is_fraud"}
    require(fields <= spec.keys(), f"spec: missing required fields {sorted(fields - spec.keys())}")
    for key in ("campaign_id", "family", "fraud_type", "vpa_strategy"):
        require(isinstance(spec[key], str) and spec[key].strip(), f"spec.{key}: expected nonempty string")
    require(spec["campaign_id"] == row.get("campaign_id"), "spec.campaign_id: identity mismatch")
    require(spec["fraud_type"] == row.get("kind") and spec["fraud_type"] in ("known", "unknown"),
            "spec.fraud_type: workload mismatch")
    require(spec["family"] in ("high_value_burst", "slow_drain", "gradual_escalation",
                              "beneficiary_hopping"), "spec.family: unsupported family")
    require(spec["vpa_strategy"] in ("single_compromised_vpa", "small_vpa_pool",
                                   "vpa_rotation", "mixed_reuse"), "spec.vpa_strategy: unsupported strategy")
    require(number(spec["target_amount"], "spec.target_amount") > 0,
            "spec.target_amount: must be positive")
    for key in ("policy_seed", "timer_seed", "vpa_seed"):
        require(type(spec[key]) is int, f"spec.{key}: expected integer seed")
    require(type(spec["is_fraud"]) is bool, "spec.is_fraud: expected boolean")
    expected_time = "spec.start_time: expected YYYY-MM-DDTHH:MM:SS[.ffffff], naive simulated UTC"
    require(isinstance(spec["start_time"], str) and spec["start_time"].strip(),
            "spec.start_time: expected nonempty string")
    require(re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?",
                         spec["start_time"]) is not None, expected_time)
    try:
        start = datetime.fromisoformat(spec["start_time"])
    except ValueError as exc:
        raise ValueError(expected_time) from exc
    require(start.tzinfo is None, expected_time)


def summary_metrics(row, config, field):
    require(SUMMARY_FIELDS <= row.keys(),
            f"{field}: missing required metric fields {sorted(SUMMARY_FIELDS - row.keys())}")
    for key, expected in (("campaigns", config["campaigns"] * len(config["seeds"])),
                          ("seeds", len(config["seeds"]))):
        require(type(row[key]) is int and row[key] == expected,
                f"{field}.{key}: invalid sample count")
    metric_means({key: row[f"{key}_mean"] for key in METRICS}, config["max_steps"], field)
    for key in METRICS:
        value = row[f"{key}_seed_sd"]
        if row["seeds"] == 1:
            require(value is None, f"{field}.{key}_seed_sd: single-seed SD must be null")
        else:
            number(value, f"{field}.{key}_seed_sd", high=1 if key == "success" else None)
    for key in TIMINGS:
        count, mean = row[f"{key}_observed"], row[f"{key}_mean_observed"]
        require(type(count) is int and 0 <= count <= row["campaigns"],
                f"{field}.{key}_observed: invalid observation count")
        if count == 0:
            require(mean is None, f"{field}.{key}_mean_observed: unobserved timing must be null")
        else:
            number(mean, f"{field}.{key}_mean_observed")


def csv_numbers(row, fields, integer_fields=(), nullable=(), field="CSV"):
    """Parse emitted CSV numbers before applying the same content schema as JSON."""
    result = dict(row)
    for key in fields:
        raw = row.get(key)
        if key in nullable and raw == "":
            result[key] = None
            continue
        try:
            value = float(raw)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{field}.{key}: expected a finite numeric value") from exc
        number(value, f"{field}.{key}", low=None)
        if key in integer_fields:
            require(value.is_integer(), f"{field}.{key}: expected integer")
            value = int(value)
        result[key] = value
    return result


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    def pairs(items):
        out = {}
        for key, value in items:
            require(key not in out, f"Duplicate JSON key: {key}")
            out[key] = value
        return out
    def invalid(value):
        raise ValueError(f"Non-finite JSON value: {value}")
    return json.loads(Path(path).read_text(), object_pairs_hook=pairs, parse_constant=invalid)


def identity(config):
    require(isinstance(config, dict), "Missing configuration object")
    for key in ("campaigns", "episodes", "max_steps"):
        require(type(config.get(key)) is int and config[key] > 0, f"Invalid config {key}")
    seeds = config.get("seeds")
    require(isinstance(seeds, list) and seeds and all(type(x) is int for x in seeds)
            and len(set(seeds)) == len(seeds), "Invalid seed inventory")
    require(config.get("detector") in ("both", "xgboost", "random_forest"), "Invalid detector")
    require(config.get("attacker") in ("all", "rl"), "Checker reference must include trained RL policies")
    names = ["xgboost", "random_forest"] if config["detector"] == "both" else [config["detector"]]
    actors = ["static", "adaptive", "rl", "untrained_rl"] if config["attacker"] == "all" else ["rl"]
    return names, actors, seeds


def validate_directory(directory, reference, require_policies):
    config = read_json(directory / "config.json")
    names, actors, seeds = identity(config)
    require(config == reference, f"Configuration mismatch: {directory}")
    manifest = read_json(directory / "manifest.json")
    require(isinstance(manifest, dict) and manifest.get("protocol") == "academic-prototype-v1",
            "Invalid manifest schema/protocol")
    required_sources = {"run_prototype.py"} | {str(p.relative_to(ROOT)) for p in (ROOT / "src").rglob("*.py")}
    sources = manifest.get("source_sha256")
    require(isinstance(sources, dict) and set(sources) == required_sources,
            "Required source coverage empty, missing or unexpected")
    require(all(isinstance(v, str) and len(v) == 64 and digest(ROOT/k) == v
                for k, v in sources.items()), "Source identity mismatch")
    require(manifest.get("dependency_lock_sha256") == digest(ROOT / "requirements-milestone1.lock"),
            "Dependency-lock identity mismatch")
    runs = manifest.get("runs")
    expected_runs = {(n, s) for n in names for s in seeds}
    require(isinstance(runs, list) and len(runs) == len(expected_runs)
            and all(isinstance(r, dict) for r in runs), "Missing/invalid manifest runs")
    require({(r.get("detector"), r.get("seed")) for r in runs} == expected_runs,
            "Manifest run identity mismatch")
    for run in runs:
        require(type(run.get("evaluation_updates")) is int and run["evaluation_updates"] == 0,
                "Evaluation learning updates are not zero")
    expected_policy = {f"q_{n}_{s}.json" for n, s in expected_runs}
    if require_policies:
        require({p.name for p in directory.glob("q_*.json")} == expected_policy,
                "Expected policy files missing or unexpected")
        for run in runs:
            name, seed = run["detector"], run["seed"]
            path = directory / f"q_{name}_{seed}.json"
            policy = read_json(path)
            require(isinstance(policy, dict) and isinstance(policy.get("q"), dict)
                    and type(policy.get("updates")) is int, "Malformed policy schema")
            from src.attackers.q_learning import QLearningAttacker
            from src.experiments.prototype import PrototypeConfig, validate_lineage
            loaded = QLearningAttacker.load(path)
            options = PrototypeConfig(**{**config, "seeds": tuple(config["seeds"])})
            model_digest = digest(ROOT / "models" / f"baseline_{name}.pkl")
            validate_lineage(loaded.metadata, name, seed, model_digest, options)
            require(run.get("model_sha256") == model_digest, "Model identity mismatch")
            require(run.get("train_seed") == loaded.metadata["training_seed"]
                    and run.get("training_families") == loaded.metadata["training_families"],
                    "Manifest policy lineage mismatch")
            if "policy_sha256" in run:
                require(run["policy_sha256"] == digest(path)
                        and run.get("verified_provenance") == loaded.metadata,
                        "Policy hash or provenance mismatch")
    rows = read_json(directory / "campaigns.json")
    expected_ids = {(n, s, k, a, f"{s}-{k}-{i:04d}")
                    for n in names for s in seeds for k in ("known", "unknown")
                    for a in actors for i in range(config["campaigns"])}
    require(isinstance(rows, list) and len(rows) == len(expected_ids), "Campaign count mismatch")
    found = []
    transaction_count = 0
    for row in rows:
        require(isinstance(row, dict) and isinstance(row.get("metrics"), dict)
                and isinstance(row.get("spec"), dict) and isinstance(row.get("outcome"), dict)
                and isinstance(row.get("transactions"), list), "Malformed campaign record")
        found.append(tuple(row.get(k) for k in ("detector", "seed", "kind", "attacker", "campaign_id")))
        specification(row["spec"], row)
        ts, m = row["transactions"], row["metrics"]
        metric_means(m, config["max_steps"], "campaign.metrics")
        require(type(m.get("success")) is int and m["success"] in (0, 1), "Invalid success metric")
        for key in ("attempted", "allowed", "flagged", "blocked", "proposals", "rejected_before_execution"):
            require(type(m.get(key)) is int and m[key] >= 0, f"Invalid metric {key}")
        require(m["attempted"] == len(ts) == m["allowed"]+m["flagged"]+m["blocked"]
                and m["proposals"] == len(ts)+m["rejected_before_execution"], "Transaction count mismatch")
        require(type(m.get("exposure")) in (int, float) and math.isfinite(m["exposure"])
                and m["exposure"] >= 0, "Invalid exposure")
        number(m.get("attempted_amount"), "campaign.metrics.attempted_amount")
        require(m["exposure"] <= m["attempted_amount"] + 1e-6,
                "campaign.metrics.exposure: exceeds attempted amount")
        for key in TIMINGS:
            require(key in m, f"campaign.metrics.{key}: missing")
            if m[key] is not None:
                number(m[key], f"campaign.metrics.{key}")
        require("reward" in m, "campaign.metrics.reward: missing")
        if m["reward"] is not None:
            number(m["reward"], "campaign.metrics.reward", low=None)
        for t in ts:
            require(isinstance(t, dict) and t.get("decision") in ("ALLOW", "FLAG", "BLOCK")
                    and type(t.get("amount")) in (int, float) and math.isfinite(t["amount"])
                    and t["amount"] > 0 and type(t.get("amount_transferred")) in (int, float)
                    and 0 <= t["amount_transferred"] <= t["amount"], "Malformed transaction")
        transaction_count += len(ts)
    require(len(set(found)) == len(found) and set(found) == expected_ids,
            "Duplicate/missing/mismatched campaign identities")
    summaries = read_json(directory / "summary.json")
    expected_summary = {(n, k, a) for n in names for k in ("known", "unknown") for a in actors}
    require(isinstance(summaries, list) and len(summaries) == len(expected_summary)
            and all(isinstance(x, dict) for x in summaries), "Summary schema/count mismatch")
    require({(x.get("detector"), x.get("kind"), x.get("attacker")) for x in summaries} == expected_summary,
            "Summary identities mismatch")
    require(all(x.get("campaigns") == config["campaigns"]*len(seeds)
                and x.get("seeds") == len(seeds) for x in summaries), "Summary sample-size mismatch")
    for row in summaries:
        summary_metrics(row, config, "summary.json")
    for filename, count in (("summary.csv", len(summaries)),
                            ("per_seed.csv", len(expected_summary)*len(seeds)),
                            ("transactions.csv", transaction_count)):
        with (directory / filename).open() as stream:
            reader = csv.DictReader(stream)
            csv_rows = list(reader)
            required_columns = {
                "summary.csv": {"detector", "kind", "attacker"} | SUMMARY_FIELDS,
                "per_seed.csv": {"detector", "kind", "attacker", "seed", "n"} | set(METRICS),
                "transactions.csv": {"detector", "seed", "attacker", "kind", "campaign_id",
                                     "step", "amount", "decision", "amount_transferred"},
            }[filename]
            require(required_columns <= set(reader.fieldnames or []), f"{filename} column schema mismatch")
            require(len(reader.fieldnames or []) == len(set(reader.fieldnames or [])),
                    f"{filename}: duplicate column names")
        require(len(csv_rows) == count and all(csv_rows), f"{filename} schema/count mismatch")
        require(all(None not in x for x in csv_rows), f"{filename}: unexpected extra CSV fields")
        if filename == "summary.csv":
            require({(x["detector"], x["kind"], x["attacker"]) for x in csv_rows} == expected_summary,
                    "summary.csv: identities mismatch")
            ints = {"campaigns", "seeds"} | {f"{key}_observed" for key in TIMINGS}
            nullable = {f"{key}_seed_sd" for key in METRICS} | {f"{key}_mean_observed" for key in TIMINGS}
            for row in csv_rows:
                parsed = csv_numbers(row, SUMMARY_FIELDS, ints, nullable, filename)
                summary_metrics(parsed, config, filename)
        if filename == "per_seed.csv":
            for row in csv_rows:
                parsed = csv_numbers(row, set(METRICS) | {"n"}, {"n"}, field=filename)
                metric_means(parsed, config["max_steps"], filename)
                require(parsed["n"] == config["campaigns"], "per_seed.csv.n: sample count mismatch")
            require({(x["detector"], int(x["seed"]), x["kind"], x["attacker"])
                     for x in csv_rows} == {(n,s,k,a) for n in names for s in seeds
                     for k in ("known","unknown") for a in actors}
                    and all(int(x["n"]) == config["campaigns"] for x in csv_rows),
                    "Per-seed identities/sample counts mismatch")
    for row in rows:
        if row["attacker"] not in ("rl", "untrained_rl"):
            continue
        for transaction in row["transactions"]:
            transition = transaction.get("rl_transition")
            require(isinstance(transition, dict) and
                    all(isinstance(transition.get(k), list) and len(transition[k]) == 3
                        and all(type(v) is int and 0 <= v <= 3 for v in transition[k])
                        for k in ("state", "next_state"))
                    and type(transition.get("action")) is int and 0 <= transition["action"] < 16
                    and type(transition.get("reward")) in (int,float)
                    and math.isfinite(transition["reward"])
                    and type(transition.get("terminal")) is bool
                    and transition.get("training") is False, "Malformed evaluation RL transition")
    with (directory / "learning.csv").open() as stream:
        learning = list(csv.DictReader(stream))
    expected_learning = config["episodes"]*len(expected_runs) if require_policies else 0
    require(len(learning) == expected_learning, "Training episode count mismatch")
    if require_policies:
        require({(x.get("detector"), int(x["seed"]), int(x["episode"])) for x in learning}
                == {(n,s,i) for n,s in expected_runs for i in range(1,config["episodes"]+1)},
                "Training episode identities mismatch")
    return manifest, expected_policy


def verify(reference, repeat, reload):
    config = read_json(reference / "config.json")
    manifest, policies = validate_directory(reference, config, True)
    validate_directory(repeat, config, True)
    loaded, _ = validate_directory(reload, config, False)
    ref_runs = {(r["detector"], r["seed"]): r for r in manifest["runs"]}
    for run in loaded["runs"]:
        original = ref_runs[(run["detector"], run["seed"])]
        for key in ("policy_sha256", "verified_provenance"):
            if key in original:
                require(run.get(key) == original[key], f"Reload {key} identity mismatch")
    report = dict(repeat={}, reload={}, policies={}, source_identity={},
                  evidence_complete=True, scientific_validity=False)
    for group, names, other in (("repeat", REPEATED, repeat), ("reload", COMMON, reload),
                                ("policies", sorted(policies), repeat)):
        for name in names:
            a, b = (reference/name).read_bytes(), (other/name).read_bytes()
            report[group][name] = dict(equal=a == b, sha256=hashlib.sha256(a).hexdigest())
    report["source_identity"] = {name: dict(equal=digest(ROOT/name) == expected)
                                 for name, expected in manifest["source_sha256"].items()}
    report["byte_equal"] = all(e["equal"] for group in ("repeat", "reload", "policies")
                                for e in report[group].values())
    report["passed"] = report["evidence_complete"] and report["byte_equal"]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("reference", "repeat", "reload", "output"):
        parser.add_argument("--"+name, type=Path, required=True)
    args = parser.parse_args()
    try:
        report = verify(args.reference, args.repeat, args.reload)
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        report = dict(passed=False, evidence_complete=False, byte_equal=None,
                      scientific_validity=False, error=str(exc))
    with args.output.open("x") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
    print(json.dumps({k: report.get(k) for k in
                      ("passed", "evidence_complete", "byte_equal", "scientific_validity", "error")}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
