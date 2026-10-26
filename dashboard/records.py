"""Strict evidence adapters and deterministic metric calculations."""
import csv
from datetime import datetime
from decimal import Decimal
import hashlib
import io
import json
import math
from pathlib import Path
import re
import statistics
import threading

LIMITATION = "This is a synthetic research environment. Results do not establish real-world UPI fraud-detection effectiveness."
DETECTORS = ("xgboost", "random_forest")
ARMS = ("static", "rule", "rl", "blind_rl", "zero_q", "adaptive", "untrained_rl")
FAMILIES = ("high_value_burst", "slow_drain", "gradual_escalation", "beneficiary_hopping")


def load(path):
    def bad(value):
        raise ValueError(f"Non-finite JSON number: {value}")
    return json.loads(Path(path).read_text(), parse_constant=bad)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def number(value, field, lower=0, upper=None):
    require(type(value) in (int, float) and math.isfinite(value),
            f"{field}: expected finite number")
    require(value >= lower and (upper is None or value <= upper), f"{field}: outside range")
    return value


def paise(value, field):
    number(value, field)
    exact = Decimal(str(value)) * 100
    require(exact == exact.to_integral_value(), f"{field}: more than two decimal places")
    return int(exact)


def timestamp(value):
    require(isinstance(value, str) and re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?", value),
        "timestamp: expected complete naive simulated-UTC timestamp")
    return datetime.fromisoformat(value)


def normalize(row, kind, source, line, index):
    require(isinstance(row, dict), f"{source}:{line}: campaign must be an object")
    if kind == "pilot":
        context = row.get("context")
        require(isinstance(context, dict), "context: required object")
        campaign_id, family, arm = context.get("id"), context.get("family"), row.get("arm")
        block, success = row.get("block"), row.get("success")
        target = number(context.get("target_paise"), "context.target_paise", 1)
        require(type(target) is int, "context.target_paise: expected integer")
        gross = number(row.get("gross_paise"), "gross_paise")
        reason, start = row.get("reason"), context.get("start")
    else:
        spec, metrics = row.get("spec"), row.get("metrics")
        require(isinstance(spec, dict) and isinstance(metrics, dict), "spec/metrics required")
        campaign_id, family, arm = row.get("campaign_id"), row.get("family"), row.get("attacker")
        block, success = row.get("seed"), metrics.get("success")
        target = paise(spec.get("target_amount"), "spec.target_amount")
        gross = paise(metrics.get("exposure"), "metrics.exposure")
        reason, start = metrics.get("termination"), spec.get("start_time")
    require(type(success) is int and success in (0, 1), "success: expected 0 or 1")
    require(type(block) is int and block >= 0, "seed/block: expected nonnegative integer")
    require(isinstance(campaign_id, str) and campaign_id, "campaign identity missing")
    require(family in FAMILIES and arm in ARMS and row.get("detector") in DETECTORS,
            "Unsupported family, strategy or detector identity")
    require(isinstance(reason, str) and reason, "termination reason missing")
    begin = timestamp(start)
    transactions = row.get("transactions")
    require(isinstance(transactions, list), "transactions: expected array")
    counts, moved, terminal, previous, timeline = dict(ALLOW=0, FLAG=0, BLOCK=0), 0, False, begin, []
    for i, tx in enumerate(transactions):
        require(isinstance(tx, dict), "transaction: expected object")
        require(not terminal, "transaction after terminal transition")
        decision = tx.get("decision")
        require(decision in counts, "transaction.decision: expected ALLOW, FLAG or BLOCK")
        amount = paise(tx.get("amount"), "transaction.amount")
        transferred = paise(tx.get("amount_transferred"), "transaction.amount_transferred")
        require(transferred <= amount, "transferred exceeds proposed amount")
        require(decision != "BLOCK" or transferred == 0, "BLOCK transaction transferred money")
        now = timestamp(tx.get("timestamp"))
        require(now >= previous, "transaction time moved backwards")
        counts[decision] += 1
        moved += transferred
        transition = tx.get("rl_transition", {})
        require(isinstance(transition, dict), "rl_transition: expected object")
        terminal = transition.get("terminal") is True
        timeline.append(dict(step=i + 1, time=tx["timestamp"], gap=(now-previous).total_seconds(),
            elapsed=(now-begin).total_seconds(), amount=amount/100, transferred=transferred/100,
            decision=decision, score=tx.get("risk_score"), terminal=terminal))
        previous = now
    require(moved == gross, "campaign gross disagrees with transaction source debits")
    return dict(index=index, campaign_id=campaign_id, detector=row["detector"], family=family,
        strategy=arm, block=block, success=success, target=target/100, gross=moved/100,
        attempts=len(transactions), counts=counts, reason=reason, start=start,
        source=source, source_line=line, raw=row, timeline=timeline)


def select(rows, filters):
    keys = ("detector", "strategy", "family", "block")
    return [r for r in rows if all(not filters.get(k) or str(r[k]) == str(filters[k]) for k in keys)
            and (not filters.get("outcome") or
                 ("completed" if r["success"] else "stopped") == filters["outcome"])]


def aggregate(rows):
    grouped = {}
    for row in rows:
        grouped.setdefault((row["detector"], row["family"], row["strategy"]), []).append(row)
    output = []
    for (detector, family, arm), group in sorted(grouped.items()):
        by_block = {}
        for r in group:
            by_block.setdefault(r["block"], []).append(r["success"])
        rates = [statistics.mean(x) for x in by_block.values()]
        n, completed = len(group), sum(r["success"] for r in group)
        counts = {k.lower(): sum(r["counts"][k] for r in group) for k in ("ALLOW", "FLAG", "BLOCK")}
        output.append(dict(detector=detector, family=family, strategy=arm, campaigns=n,
            completed=completed, completion=100*completed/n, blocks=len(rates),
            block_sd=100*statistics.stdev(rates) if len(rates) > 1 else None,
            mean_attempts=statistics.mean(r["attempts"] for r in group),
            gross=sum(r["gross"] for r in group), **counts))
    return output


def totals(rows):
    return dict(campaigns=len(rows), completed=sum(r["success"] for r in rows),
        transactions=sum(r["attempts"] for r in rows),
        gross=round(sum(r["gross"] for r in rows), 2),
        **{k.lower(): sum(r["counts"][k] for r in rows) for k in ("ALLOW", "FLAG", "BLOCK")})


def csv_export(rows):
    fields = ("detector", "family", "strategy", "campaigns", "completed", "completion",
              "blocks", "block_sd", "allow", "flag", "block", "mean_attempts", "gross")
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        safe = {k: ("'" + str(v) if isinstance(v, str) and v[:1] in "=+-@\t\r" else v)
                for k, v in row.items()}
        writer.writerow(safe)
    return out.getvalue()


class Catalog:
    def __init__(self, root, repo, state):
        self.root, self.repo, self.state = Path(root), Path(repo), Path(state)
        self.imported = load(self.root / "index.json") if (self.root / "index.json").exists() else {}
        self.files, self.cache, self.lock = {}, {}, threading.RLock()

    def register(self, path):
        p = Path(path).resolve()
        bases = (self.root.resolve(), self.state.resolve(), self.repo.resolve(),
                 (self.root.parent / "reports").resolve())
        require(any(p.is_relative_to(b) for b in bases) and p.is_file() and not path.is_symlink(),
                "Artifact is outside approved evidence roots")
        require(not any(part.startswith(".") for part in p.relative_to(
            next(b for b in bases if p.is_relative_to(b))).parts), "Hidden files are not available")
        token = hashlib.sha256(str(p).encode()).hexdigest()[:24]
        with self.lock:
            self.files[token] = p
        return dict(id=token, name=p.name, bytes=p.stat().st_size,
                    url=f"/api/files/{token}")

    def descriptors(self):
        result = []
        for name, record in self.imported.items():
            result.append(dict(id=name, label=name, kind=record["kind"], retained=True,
                path=self.root/name, execution=record.get("execution")))
        runs = self.state / "runs"
        if runs.exists():
            for path in sorted(runs.iterdir()):
                if path.is_dir() and (path/"manifest.json").is_file():
                    manifest = load(path/"manifest.json")
                    result.append(dict(id="run-"+path.name, label=path.name,
                        kind="pilot" if manifest.get("protocol") == "mechanism-pilot-v1" else "legacy",
                        retained=False, path=path, execution=None))
        return result

    def descriptor(self, run):
        found = next((x for x in self.descriptors() if x["id"] == run), None)
        require(found is not None, "Unknown run identifier")
        return found

    def list(self):
        return [{k: v for k, v in x.items() if k != "path"} for x in self.descriptors()]

    def dataset(self, run):
        d = self.descriptor(run)
        path = d["path"]
        names = self.imported[run]["files"] if d["retained"] else {
            str(p.relative_to(path)): None for p in path.rglob("*") if p.is_file()}
        signature = tuple((name, (path/name).stat().st_size, (path/name).stat().st_mtime_ns)
                          for name in sorted(names))
        with self.lock:
            if run in self.cache and self.cache[run]["signature"] == signature:
                return self.cache[run]
        if d["retained"]:
            for name, expected in self.imported[run]["files"].items():
                require(sha(path/name) == expected, f"Retained artifact integrity failed: {name}")
        config, manifest = load(path/"config.json"), load(path/"manifest.json")
        require(isinstance(config, dict) and isinstance(manifest, dict), "config/manifest must be objects")
        sources = sorted(path.glob("block-*/*/campaigns.jsonl")) if d["kind"] == "pilot" else [path/"campaigns.json"]
        require(bool(sources), "No campaign record files")
        records = []
        for source in sources:
            items = [json.loads(s, parse_constant=lambda x: (_ for _ in ()).throw(
                ValueError("Nonfinite record"))) for s in source.read_text().splitlines()] if source.suffix == ".jsonl" else load(source)
            require(isinstance(items, list), "campaign records must be an array")
            artifact = self.register(source)
            for i, row in enumerate(items):
                records.append(normalize(row, d["kind"], artifact, i+1, len(records)))
        require(bool(records), "No campaigns recorded")
        identities = [(r["detector"], r["strategy"], r["campaign_id"]) for r in records]
        require(len(identities) == len(set(identities)), "Duplicate campaign identity")
        if d["kind"] == "pilot":
            expected = config["blocks"] * config["contexts"] * 2 * 2 * 5
            require(manifest.get("evaluation_campaigns") == expected == len(records), "Campaign count mismatch")
        else:
            expected = (2 * config["campaigns"] * len(config["seeds"])
                        * (2 if config["detector"] == "both" else 1)
                        * (4 if config["attacker"] == "all" else 1))
            require(expected == len(records), "Legacy campaign count mismatch")
        benign = []
        if d["kind"] == "pilot":
            for item in manifest["blocks"]:
                bp = path/f"block-{item['block']:02d}"/item["detector"]/"benign_scores.json"
                for stratum, episodes in load(bp).items():
                    require(stratum in ("benign_test", "benign_mimic_test"), "Unknown benign stratum")
                    for e in episodes:
                        number(e.get("peak"), "benign peak", upper=1)
                    benign.append(dict(detector=item["detector"], block=item["block"],
                        stratum=stratum, n=len(episodes),
                        blocked=sum(e["peak"] >= item["block_threshold"] for e in episodes),
                        alerted=sum(e["peak"] >= item["flag"] for e in episodes),
                        source=self.register(bp)))
        proof = None
        if d["retained"]:
            proofpath = self.root/self.imported[run]["verification"]
            result = load(proofpath)
            passed = (result.get("evidence_complete") is True and
                      result.get("passed", True) is True and not result.get("errors"))
            proof = dict(result=result, artifact=self.register(proofpath),
                         label=("Imported verifier PASS; retained hashes matched" if passed
                                else "Imported verifier FAIL / unavailable"))
        value = dict(records=records, config=config, manifest=manifest, benign=benign,
                     descriptor=d, proof=proof, signature=signature)
        with self.lock:
            if len(self.cache) >= 2:
                self.cache.pop(next(iter(self.cache)))
            self.cache[run] = value
        return value

    def view(self, run, filters):
        data = self.dataset(run)
        proof = data["proof"]
        # Attach only completed local verifier results naming this exact run.
        for jobfile in sorted((self.state/"jobs").glob("*.json"), reverse=True):
            job = load(jobfile)
            if job.get("kind") != "verify" or job.get("status") != "completed" or job.get("exit_code") != 0:
                continue
            argv = job.get("argv", [])
            inputs = [argv[argv.index(k)+1] for k in ("--reference", "--repeat", "--reload") if k in argv]
            if str(data["descriptor"]["path"]) not in inputs:
                continue
            if max((n[2] for n in data["signature"]), default=0)/1e9 > datetime.fromisoformat(job["end"]).timestamp():
                continue
            result = job.get("verification", {})
            if result.get("evidence_complete") is True:
                proof = dict(result=result, label="Local verifier PASS; exact inputs in execution log",
                    artifact=self.register(Path(job["output"])/"verification.json"))
                break
        selected = select(data["records"], filters)
        benign = [b for b in data["benign"] if
                  (not filters.get("detector") or b["detector"] == filters["detector"]) and
                  (not filters.get("block") or str(b["block"]) == filters["block"])]
        combined = {}
        for b in benign:
            group = combined.setdefault((b["detector"], b["stratum"]), dict(n=0, blocked=0, alerted=0, sources=[]))
            for key in ("n", "blocked", "alerted"):
                group[key] += b[key]
            group["sources"].append(b["source"])
        benign_groups = [dict(detector=d, stratum=s, rate=100*v["blocked"]/v["n"], **v)
                         for (d, s), v in combined.items() if v["n"]]
        return dict(run=run, kind=data["descriptor"]["kind"], totals=totals(selected),
            groups=aggregate(selected), benign=benign_groups, config=data["config"],
            proof=proof, filters=filters,
            options={k: sorted({str(r[k]) for r in data["records"]}) for k in
                     ("detector", "strategy", "family", "block")},
            sources=[self.register(data["descriptor"]["path"]/"manifest.json")],
            limitation=LIMITATION)

    def campaigns(self, run, filters, offset=0):
        rows = select(self.dataset(run)["records"], filters)
        return dict(total=len(rows), offset=offset, rows=[
            {k: v for k, v in r.items() if k not in ("raw", "timeline")}
            for r in rows[offset:offset+50]])

    def models(self, run):
        data = self.dataset(run)
        path, output = data["descriptor"]["path"], []
        if data["descriptor"]["kind"] == "pilot":
            for entry in data["manifest"]["blocks"]:
                folder = path/f"block-{entry['block']:02d}"/entry["detector"]
                binding = load(folder/"fit_binding.json")
                output.append(dict(detector=entry["detector"], block=entry["block"],
                    sha256=sha(folder/"model.pkl"), provenance="Registered new fit; not external attestation",
                    fitting=len(binding["fit_episode_ids"]), validation=binding.get("validation_auc"),
                    held_out="Declared GE generator/ancestry/prefix only",
                    binding=self.register(folder/"fit_binding.json"),
                    policies=[dict(name=p.name, sha256=sha(p), source=self.register(p))
                              for p in (folder/"rl.json", folder/"blind_rl.json") if p.exists()],
                    membership=self.register(folder.parent/"episodes.json"),
                    evaluation=self.register(folder.parent/"evaluation_plan.json")))
        else:
            for p in sorted((self.repo/"models").glob("*.pkl")):
                output.append(dict(detector="xgboost" if "xgboost" in p.name else "random_forest",
                    filename=p.name, block=None, sha256=sha(p), fitting=None,
                    validation=None, provenance="Historical training-family ancestry unverified",
                    held_out="Not established", binding=None, membership=None))
        return output

    def datasets(self, run):
        data = self.dataset(run)
        path = data["descriptor"]["path"]
        paths = sorted(path.glob("block-*/*.csv")) + sorted(path.glob("block-*/episodes.json"))
        if data["descriptor"]["kind"] == "legacy":
            paths = sorted((self.repo/"data").glob("*.csv"))
        return [dict(name=str(p.relative_to(path) if p.is_relative_to(path) else p.relative_to(self.repo)),
                     sha256=sha(p), bytes=p.stat().st_size, source=self.register(p),
                     role=("Registered membership" if p.suffix == ".json" else
                           "Fit" if p.name == "fit_rows.csv" else
                           "Validation" if p.name == "validation_rows.csv" else
                           "Historical file; detector ancestry unverified")) for p in paths]
