"""Independent raw-record checker/recalculator. Does not import project helpers."""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import random
import statistics

BANDS = (1000, 3000, 8000, 15000)
ARMS = ("static", "rule", "rl", "blind_rl", "zero_q")


def load(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", required=True)
    parser.add_argument("--repeat")
    parser.add_argument("--reload")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(args.reference)
    cfg, manifest = load(root/"config.json"), load(root/"manifest.json")
    errors, checks, replayed = [], 0, 0
    tables, paired = defaultdict(list), defaultdict(dict)
    records_count = 0
    benign_tables, verified_bindings = [], []

    def check(ok, detail):
        nonlocal checks
        checks += 1
        if not ok and len(errors) < 100:
            errors.append(detail)

    def stop_if_invalid():
        if errors:
            result = dict(evidence_complete=False, checks=checks, errors=errors,
                          td_updates_replayed=replayed, scientific_validity="NOT ESTABLISHED", gate_c="HOLD")
            with Path(args.output).open("x") as f:
                json.dump(result,f,indent=2)
            print(json.dumps(result))
            raise SystemExit(1)

    supplied = [root.resolve()] + [Path(p).resolve() for p in (args.repeat,args.reload) if p]
    check(len(set(supplied)) == len(supplied), "Distinct run directories required")
    if args.repeat or args.reload:
        check(manifest.get("mode") == "fit", "Reference must be a fit run for triplet verification")
    for role, alternative, expected_mode in (("repeat",args.repeat,"fit"),("reload",args.reload,"reload")):
        if alternative:
            other_manifest = load(Path(alternative)/"manifest.json")
            check(other_manifest.get("mode") == expected_mode, f"{role} manifest mode must be {expected_mode}")
            check(load(Path(alternative)/"config.json") == cfg, f"{role} configuration identity")
            if role == "reload":
                check(other_manifest.get("training_episodes_executed") == 0, "Reload must execute zero training episodes")
    stop_if_invalid()

    source = load(root/"source.json")
    project = Path(__file__).resolve().parent
    expected_source = {str(p.relative_to(project)) for p in (project/"src").rglob("*.py")}
    expected_source.update(("requirements-milestone1.lock", "docs/MECHANISM_PILOT_DESIGN.md"))
    check(set(source) == expected_source, "Source coverage")
    check(source == manifest["source_sha256"], "Source manifest binding")
    check(all((project/p).is_file() and sha(project/p)==h for p,h in source.items()), "Actual source identity")

    def legal(family, previous, repeats):
        if family == "high_value_burst":
            bands = [3] if previous == -1 else [2, 3]
        else:
            bands = [0] if previous == -1 else ([3] if previous == 3 else
                    ([previous+1] if repeats >= 2 else [previous, previous+1]))
        return [2*b + p for b in bands for p in (0, 1)]

    def feature_rows(episode):
        times, values = [], []
        for e in episode["events"]:
            t = datetime.fromisoformat(e["time"])
            values.append([e["paise"]/100, t.hour,
                sum(0 <= (t-old).total_seconds() < 3600 for old in times), int(not times)])
            times.append(t)
        return values

    def forbidden(events):
        if not events or events[0]["band"] != 0:
            return False
        prev, repetitions = 0, 1
        for e in events[1:]:
            b = e["band"]
            if b not in (prev, prev+1) or (b == prev and repetitions >= 2):
                return False
            if b > prev:
                return True
            repetitions += 1
        return False

    def inspect(record, thresholds, q=None):
        nonlocal replayed
        ctx, txs = record["context"], record["transactions"]
        moved, old_decision, previous, repeats = 0, 0, -1, 0
        times = []
        check(record["proposals"] == len(txs), "Unexpected rejected proposal")
        bonuses = 0
        for index, tx in enumerate(txs):
            tr = tx["rl_transition"]
            action = tr["action"]
            mask = legal(ctx["family"], previous, repeats)
            check(tr["legal_mask"] == mask and action in mask, "Illegal/mismatched action mask")
            band, pace = action//2, (300, 1200)[action % 2]
            check(tr["action_parameters"] == [BANDS[band], pace], "Action schema")
            expected = min(BANDS[band]*100, ctx["target_paise"]-moved)
            check(Decimal(str(tx["amount"]))*100 == expected, "Final clipping / amount")
            t = datetime.fromisoformat(tx["timestamp"])
            start = datetime.fromisoformat(ctx["start"])
            check((t-start).total_seconds() <= 86400, "Duration")
            check((not times and t == start) or
                  (bool(times) and (t-times[-1]).total_seconds() == pace), "Pacing")
            vector = {"amount": expected/100, "hour_of_day": t.hour,
                "velocity_1h": sum(0 <= (t-old).total_seconds() < 3600 for old in times),
                "is_new_vpa": int(not times)}
            check(vector == tx["computed_features"], "Feature/train-inference semantic mismatch")
            times.append(t)
            flag, block = thresholds
            score = tx["risk_score"]
            decision = "BLOCK" if score >= block else "FLAG" if score >= flag else "ALLOW"
            check(decision == tx["decision"], "Threshold decision")
            transferred = 0 if decision == "BLOCK" else expected
            check(Decimal(str(tx["amount_transferred"]))*100 == transferred, "Execution transfer")
            state = (min(3, 4*moved//ctx["target_paise"]), min(3, 4*(30-index)//30),
                     0 if record["arm"] in ("static", "blind_rl") else old_decision)
            check(tr["state"] == list(state), "State observation")
            moved += transferred
            complete = moved == ctx["target_paise"]
            terminal = complete or decision == "BLOCK" or index == 29
            check(tr["terminal"] == terminal, "Terminal outcome")
            check(not terminal or index == len(txs)-1, "Transaction after terminal")
            bonuses += int(complete)
            reward = (3*transferred/ctx["target_paise"] + 2*complete -
                      (decision == "BLOCK") - .2*(decision == "FLAG") - .02 -
                      .5*(index == 29 and not complete and decision != "BLOCK"))
            check(math.isclose(reward, tr["reward"], abs_tol=1e-12), "Reward")
            repeats = repeats + 1 if previous == band else 1
            previous = band
            old_decision = {"ALLOW":1, "FLAG":2, "BLOCK":3}[decision]
            following = (min(3,4*moved//ctx["target_paise"]),min(3,4*(29-index)//30),
                         0 if record["arm"] in ("static", "blind_rl") else old_decision)
            next_mask = [] if terminal else legal(ctx["family"], previous, repeats)
            check(tr["next_state"] == list(following), "Next state")
            check(tr["next_legal_mask"] == next_mask, "Next legal mask")
            if q is not None:
                values = q.setdefault(state, [0.]*8)
                future = 0 if terminal else max(q.setdefault(following, [0.]*8)[i] for i in next_mask)
                values[action] += .25*(reward + .95*future-values[action])
                replayed += 1
        check(bonuses <= 1, "Duplicate completion bonus")
        check(moved == record["gross_paise"] <= ctx["target_paise"], "Gross/target money")
        check(record["success"] == int(moved == ctx["target_paise"]), "Campaign success")
        check(len(txs) <= 30 and bool(txs) and txs[-1]["rl_transition"]["terminal"], "Horizon/final terminal")

    for b in range(cfg["blocks"]):
        folder = root/f"block-{b:02d}"
        registry = load(folder/"episodes.json")
        ids = [e["id"] for group in registry.values() for e in group]
        check(len(ids) == len(set(ids)), "Split episode overlap")
        for role in ("train", "validation", "calibration"):
            for e in registry[role]:
                check(e["parent"] is None and e["family"] != "gradual_escalation"
                      and not forbidden(e["events"]), "Forbidden mechanism/ancestry in development")
        fit = list(csv.DictReader((folder/"fit_rows.csv").open()))
        expected_rows = [(e["id"], i, e["label"], vector)
                         for e in registry["train"] for i, vector in enumerate(feature_rows(e))]
        check(len(fit) == len(expected_rows), "Fitter row count")
        for r, (eid, i, label, vector) in zip(fit, expected_rows):
            check(r["episode_id"] == eid and int(r["step"]) == i and int(r["label"]) == label
                  and [float(r[k]) for k in ("amount","hour_of_day","velocity_1h","is_new_vpa")] == vector,
                  "Fitter input features or membership")
        plan = load(folder/"evaluation_plan.json")
        check(len(plan) == 2*cfg["contexts"], "Evaluation plan count")
        check(not set(ids).intersection(c["id"] for c in plan), "Fit/test ID overlap")
        for algorithm in ("xgboost", "random_forest"):
            path = folder/algorithm
            binding = load(path/"fit_binding.json")
            check(binding["model_sha256"] == sha(path/"model.pkl"), "Model identity")
            check(binding["fit_rows_sha256"] == sha(folder/"fit_rows.csv"), "Data binding")
            check(binding["episode_registry_sha256"] == sha(folder/"episodes.json"), "Registry binding")
            check(binding["fit_episode_ids"] == [e["id"] for e in registry["train"]], "Observed fit membership")
            check(binding["feature_matrix_sha256"] == canonical(
                [[float(r[k]) for k in ("amount","hour_of_day","velocity_1h","is_new_vpa")] for r in fit]),
                "Fit feature matrix")
            check(binding["fitting_label_sha256"] == canonical([int(r["label"]) for r in fit]), "Fit label hash")
            verified_bindings.append(dict(block=b, detector=algorithm, model=binding["model_sha256"]))
            cal = load(path/"calibration.json")
            thresholds = cal["flag"], cal["block"]
            check(0 <= cal["flag"] < cal["block"] <= 1, "Calibrated thresholds")
            for metric, threshold, maximum in (("alert", cal["flag"],.025),("block",cal["block"],.005)):
                peaks = [max(e["scores"]) for e in cal["episodes"]]
                check(len(peaks) == cfg["calibration"] and all(math.isfinite(v) for v in peaks), "Calibration completeness")
                check(sum(p >= threshold for p in peaks)/len(peaks) <= maximum, "Calibration budget")
                check(math.isclose(statistics.mean(p >= threshold for p in peaks), cal[f"achieved_any_{metric}"]), "Calibration rate")
            for role, group in load(path/"benign_scores.json").items():
                check(len(group) == cfg["benign_test"], "Benign denominator")
                benign_tables.append(dict(block=b, detector=algorithm, stratum=role,
                    n=len(group), any_block=statistics.mean(max(e["scores"]) >= cal["block"] for e in group),
                    any_alert=statistics.mean(max(e["scores"]) >= cal["flag"] for e in group)))
            frozen = load(path/"frozen_evaluation.json")
            check(len(frozen) == 5 and {r["arm"] for r in frozen} == set(ARMS), "Frozen arm coverage")
            for f in frozen:
                check(f["before"] == f["after"] and f["updates_before"] == f["updates_after"], "Frozen full persisted policy")
                check(f["episodes"] == len(plan), "Frozen evaluation episodes")
            if manifest["mode"] == "fit":
                qtables = {"rl":{}, "blind_rl":{}}
                training_ids = defaultdict(list)
                count = 0
                for line in (path/"training.jsonl").open():
                    r = json.loads(line)
                    training_ids[r["arm"]].append(r["context"]["id"])
                    check(not r["context"]["id"] in {c["id"] for c in plan}, "RL training/test overlap")
                    check(r["context"]["family"] == "high_value_burst", "RL holdout")
                    inspect(r, thresholds, qtables[r["arm"]])
                    count += 1
                check(count == 2*cfg["episodes"], "Training episode count")
                for arm in ("rl", "blind_rl"):
                    p = load(path/(arm+".json"))
                    check(p["metadata"]["model_sha256"] == sha(path/"model.pkl"), "Policy/model lineage")
                    check(p["version"] == manifest["protocol"] and p["mode"] == arm and p["metadata"]["mode"] == arm,
                          "Policy schema/role")
                    check((p["alpha"],p["gamma"],p["epsilon"]) == (.25,.95,0.) and p["metadata"]["source_sha256"] == source,
                          "Policy parameters/source lineage")
                    check(p["metadata"]["training_context_ids"] == training_ids[arm], "Policy training lineage")
                    q = {tuple(map(int,k.split(","))):v for k,v in p["q"].items()}
                    check(q.keys() == qtables[arm].keys(), "TD table support")
                    check(all(all(math.isclose(a,c,rel_tol=1e-12,abs_tol=1e-12)
                        for a,c in zip(q[k],qtables[arm][k])) for k in q), "All recorded TD updates replay")
                    check(p["updates"] == sum(len(json.loads(line)["transactions"])
                        for line in (path/"training.jsonl").open() if json.loads(line)["arm"] == arm),
                        "TD count")
            else:
                check((path/"training.jsonl").stat().st_size == 0, "Reload must not train")
            identities = set()
            for line in (path/"campaigns.jsonl").open():
                r = json.loads(line)
                key = (r["arm"], r["context"]["id"])
                check(key not in identities and r["context"] in plan, "Duplicate/unplanned evaluation")
                identities.add(key)
                inspect(r, thresholds)
                group = (r["detector"], r["context"]["family"], r["arm"])
                tables[group].append(r)
                paired[(r["detector"],r["context"]["family"],r["block"],r["context"]["id"])][r["arm"]] = r["success"]
                records_count += 1
            check(len(identities) == 5*len(plan), "Full arm/context coverage")
    check(records_count == cfg["blocks"]*2*5*2*cfg["contexts"], "Total campaign count")
    for block in manifest["blocks"]:
        check(block["model_payload_before"] == block["model_payload_after"], "Persisted model state unchanged")
    stop_if_invalid()
    for r in load(root/"summary.json"):
        group = tables[(r["detector"],r["family"],r["arm"])]
        means = [statistics.mean(x["success"] for x in group if x["block"] == b) for b in range(cfg["blocks"])]
        check(r["n"] == len(group) and math.isclose(r["success"],statistics.mean(means),abs_tol=1e-12), "Summary success")
        sd = statistics.stdev(means) if len(means)>1 else None
        check(r["seed_sd"] is None if sd is None else math.isclose(r["seed_sd"],sd,abs_tol=1e-12), "Summary SD")
        check(math.isclose(r["gross_mean"],statistics.mean(x["gross_paise"]/100 for x in group),abs_tol=1e-8), "Summary gross")
    stop_if_invalid()
    contrasts = []
    rng = random.Random(908172)
    for detector in ("xgboost","random_forest"):
        for left,right in (("rule","static"),("rl","blind_rl"),("rl","zero_q")):
            differences = []
            for b in range(cfg["blocks"]):
                pairs = [v for k,v in paired.items() if k[:3] == (detector,"gradual_escalation",b)]
                check(len(pairs) == cfg["contexts"] and all(set(p)==set(ARMS) for p in pairs), "Pairing")
                differences.append(statistics.mean(p[left]-p[right] for p in pairs))
            samples = sorted(statistics.mean(rng.choices(differences,k=len(differences))) for _ in range(10000))
            contrasts.append(dict(detector=detector,contrast=f"{left}-{right}",block_differences=differences,
                mean=statistics.mean(differences),exploratory_percentile_interval=[samples[249],samples[9749]],
                warning="Descriptive cluster bootstrap with few blocks; no confirmatory or equivalence claim"))
    equality = {}
    for name, alternative in (("repeat",args.repeat),("reload",args.reload)):
        if not alternative:
            continue
        other = Path(alternative)
        entries = {}
        for p in root.rglob("*"):
            if not p.is_file() or p.name in ("manifest.json",):
                continue
            if name == "reload" and p.name == "training.jsonl":
                continue
            relative = p.relative_to(root)
            entries[str(relative)] = (other/relative).is_file() and sha(p)==sha(other/relative)
        check(all(entries.values()), f"{name} selected file byte equality")
        equality[name] = entries
    metrics = []
    for (detector,family,arm), group in sorted(tables.items()):
        first_blocks, first_flags, blocked_amount = [], [], 0
        for r in group:
            start = datetime.fromisoformat(r["context"]["start"])
            block_events = [t for t in r["transactions"] if t["decision"]=="BLOCK"]
            flag_events = [t for t in r["transactions"] if t["decision"]=="FLAG"]
            if block_events:
                first_blocks.append((datetime.fromisoformat(block_events[0]["timestamp"])-start).total_seconds())
            if flag_events:
                first_flags.append((datetime.fromisoformat(flag_events[0]["timestamp"])-start).total_seconds())
            blocked_amount += sum(int(Decimal(str(t["amount"]))*100) for t in block_events)
        metrics.append(dict(detector=detector,family=family,arm=arm,n=len(group),
            completion=statistics.mean(r["success"] for r in group),
            any_block=len(first_blocks)/len(group), any_flag=len(first_flags)/len(group),
            conditional_first_block_seconds=statistics.mean(first_blocks) if first_blocks else None,
            conditional_first_flag_seconds=statistics.mean(first_flags) if first_flags else None,
            blocked_proposed_paise=blocked_amount, gross_paise=sum(r["gross_paise"] for r in group),
            transactions=sum(len(r["transactions"]) for r in group),
            interpretation="Gross source debit, not unrecovered victim loss; event timing conditional on event"))
    record = dict(evidence_complete=not errors, checks=checks, errors=errors, td_updates_replayed=replayed,
        campaigns=records_count, fit_bindings=verified_bindings, scientific_validity="EXPLORATORY ONLY",
        matched_contrasts=contrasts, metrics=metrics, benign=benign_tables, equality=equality, gate_c="HOLD")
    with Path(args.output).open("x") as f:
        json.dump(record,f,indent=2,allow_nan=False)
    print(json.dumps({k:v for k,v in record.items() if k not in ("equality","benign","fit_bindings","metrics")},indent=2))
    raise SystemExit(bool(errors))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, TypeError, KeyError, FileNotFoundError, AttributeError, IndexError) as exc:
        import sys
        result = dict(evidence_complete=False, errors=[f"{type(exc).__name__}: {exc}"],
                      scientific_validity="NOT ESTABLISHED", gate_c="HOLD")
        if "--output" in sys.argv:
            target = Path(sys.argv[sys.argv.index("--output")+1])
            if not target.exists():
                target.write_text(json.dumps(result,indent=2))
        print(json.dumps(result))
        raise SystemExit(1)
