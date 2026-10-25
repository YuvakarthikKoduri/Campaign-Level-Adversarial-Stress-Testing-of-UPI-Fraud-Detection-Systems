#!/usr/bin/env python3
"""Small or large experiments use the same paired, traceable, non-overwriting runner."""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import re
import subprocess
import uuid

from src.detectors.baseline import load_detector
from src.environment import UPIEnvironment
from src.environment.thresholds import ThresholdConfig
from src.experiments.config import RunConfig, build_workload, FEATURE_SCHEMA, METRIC_VERSION
from src.experiments.scenarios import ExperimentScenarios

ROOT = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def git_output(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=["S1", "S2", "S3", "S4", "all"], default="S1")
    parser.add_argument("--campaigns", type=int, default=100)
    parser.add_argument("--detector", choices=["xgboost", "random_forest", "both"], default="xgboost")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-steps", type=int, default=50)
    parser.add_argument("--max-duration-seconds", type=float, default=86400)
    parser.add_argument("--simulated-start", default="2026-01-05T12:00:00")
    parser.add_argument("--flag-threshold", type=float, default=0.40)
    parser.add_argument("--block-threshold", type=float, default=0.70)
    parser.add_argument("--feedback", choices=["label_only", "score"], default="label_only")
    parser.add_argument("--split", choices=["development", "evaluation"], default="development")
    parser.add_argument("--development-seeds", type=int, nargs="*", default=[])
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "runs")
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args(argv)
    config = RunConfig(seed=args.seed, campaigns=args.campaigns, max_steps=args.max_steps,
                       max_duration_seconds=args.max_duration_seconds,
                       simulated_start=args.simulated_start, flag_threshold=args.flag_threshold,
                       block_threshold=args.block_threshold, feedback=args.feedback,
                       split=args.split, development_seeds=tuple(args.development_seeds))
    run_id = args.run_id or f"{datetime.now(timezone.utc):%Y%m%dT%H%M%S}-{uuid.uuid4().hex[:8]}"
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}", run_id):
        raise ValueError("Invalid run ID")
    directory = args.output_dir / run_id
    directory.mkdir(parents=True, exist_ok=False)
    models = ["xgboost", "random_forest"] if args.detector == "both" else [args.detector]
    selected = ["S1", "S2", "S3", "S4"] if args.scenario == "all" else [args.scenario]
    manifest = {
        "status": "running", "run_id": run_id, "metric_version": METRIC_VERSION,
        "actual_started_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_output("rev-parse", "HEAD"),
        "git_branch": git_output("branch", "--show-current"),
        "git_status": git_output("status", "--porcelain"),
        "python": platform.python_version(),
        "packages": {d.metadata["Name"]: d.version for d in importlib.metadata.distributions()},
        "config": config.to_dict(), "scenarios": selected, "feature_schema": FEATURE_SCHEMA,
        "model_sha256": {}, "dataset_sha256": {},
        "threshold_policy": "explicit_three_way; artifact_binary_threshold_not_applied",
        "inference_threads": 1,
        "new_vpa_semantics": "first_observed_source_vpa_before_current_attempt",
        "threat_model": "docs/MILESTONE1_CONTRACT.md",
        "claims": {"research_evaluation": False, "historical_comparability": False,
                   "unrecovered_loss_simulated": False},
    }
    save_json(directory / "manifest.json", manifest)
    try:
        for name in models:
            manifest["model_sha256"][name] = digest(ROOT / "models" / f"baseline_{name}.pkl")
        manifest["dataset_sha256"]["synthetic"] = digest(ROOT / "data/synthetic/upi_transactions_v1.csv")
        # Snapshot all source used, including uncommitted files, not just a dirty flag.
        source_paths = [ROOT / "run_experiment.py", *sorted((ROOT / "src").rglob("*.py"))]
        manifest["source_sha256"] = {str(p.relative_to(ROOT)): digest(p) for p in source_paths}
        manifest["contract_sha256"] = digest(ROOT / "docs/MILESTONE1_CONTRACT.md")
        manifest["dependency_lock_sha256"] = digest(ROOT / "requirements-milestone1.lock")
        (directory / "source.diff").write_text(git_output("diff", "HEAD", "--", "src", "run_experiment.py"))
        workload = build_workload(config)
        serialized_workload = {k: [s.to_dict() for s in specs] for k, specs in workload.items()}
        save_json(directory / "workload.json", serialized_workload)
        all_results = {}
        artifact_thresholds = {}
        for name in models:
            detector = load_detector(str(ROOT / "models" / f"baseline_{name}.pkl"))
            artifact_thresholds[name] = detector.artifact_threshold
            policy = ThresholdConfig(config.flag_threshold, config.block_threshold)
            scenarios = ExperimentScenarios(detector, UPIEnvironment(policy, detector),
                                            config=config, workload=workload)
            summaries = {s: scenarios._run(s, config.campaigns, seed=config.seed) for s in selected}
            all_results[name] = {"summary": summaries, "campaigns": scenarios.records}
            save_json(directory / f"{name}.json", all_results[name])
        canonical = {"metric_version": METRIC_VERSION, "config": config.to_dict(),
                     "workload": serialized_workload, "results": all_results}
        save_json(directory / "canonical.json", canonical)
        manifest.update(status="complete", artifact_binary_thresholds=artifact_thresholds,
                        actual_finished_utc=datetime.now(timezone.utc).isoformat(),
                        output_sha256={p.name: digest(p) for p in directory.iterdir()
                                       if p.is_file() and p.name != "manifest.json"})
    except Exception as exc:
        manifest.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        save_json(directory / "manifest.json", manifest)
    print(f"Corrected-v2 outputs: {directory}")
    for name, result in all_results.items():
        for scenario, summary in result["summary"].items():
            print(name, scenario, "success", summary["campaign_success_rate"],
                  "transferred_exposure", round(summary["total_financial_exposure"], 2))
    return directory


if __name__ == "__main__":
    main()
