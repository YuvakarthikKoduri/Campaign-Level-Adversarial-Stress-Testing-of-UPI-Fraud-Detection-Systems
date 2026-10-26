"""Permanent F5 regressions: equal malformed copies are still invalid evidence.

Run from the repository root: python -B -s -m pytest f5-evidence/test_schema.py
All experiment and mutation destinations are pytest-local; no saved evidence is edited.
"""
import csv
import datetime
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest

from src.experiments.prototype import PrototypeConfig, compare
from verify_prototype_outputs import verify

# Independent expected field inventory, not supplied by the checker under test.
METRICS = ("success", "proposals", "rejected_before_execution", "attempted",
           "allowed", "flagged", "blocked", "exposure")


@pytest.fixture(scope="session")
def valid(tmp_path_factory):
    root = tmp_path_factory.mktemp("schema-valid")
    config = PrototypeConfig(seeds=(101,), episodes=5, campaigns=2, max_steps=3)
    compare(root / "main", config)
    compare(root / "repeat", config)
    compare(root / "reload", config, policy_dir=root / "main")
    return root


@pytest.fixture(scope="session")
def valid_two_seeds(tmp_path_factory):
    root = tmp_path_factory.mktemp("schema-two-seeds")
    config = PrototypeConfig(seeds=(101, 202), episodes=3, campaigns=2, max_steps=3)
    compare(root / "main", config)
    compare(root / "repeat", config)
    compare(root / "reload", config, policy_dir=root / "main")
    return root


def copies(source, destination):
    for name in ("main", "repeat", "reload"):
        shutil.copytree(source / name, destination / name)


def mutate(root, filename, section, key, value, remove=False):
    for name in ("main", "repeat", "reload"):
        path = root / name / filename
        if filename.endswith(".json"):
            rows = json.loads(path.read_text())
            target = rows[0] if section is None else rows[0][section]
            if remove:
                del target[key]
            else:
                target[key] = value
            path.write_text(json.dumps(rows, sort_keys=True))
        else:
            with path.open() as stream:
                reader = csv.DictReader(stream)
                fields, rows = reader.fieldnames, list(reader)
            if remove:
                fields = [field for field in fields if field != key]
                for row in rows:
                    del row[key]
            else:
                rows[0][key] = value
            with path.open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
    assert len({(root / name / filename).read_bytes()
                for name in ("main", "repeat", "reload")}) == 1


def rejected(root, diagnostic):
    with pytest.raises(ValueError, match=diagnostic):
        verify(root / "main", root / "repeat", root / "reload")
    result, report = checker_cli(root)
    assert result.returncode != 0, result.stdout + result.stderr
    assert report["evidence_complete"] is False and report["passed"] is False
    assert re.search(diagnostic, report["error"]), report


def checker_cli(root):
    """Retain actual CLI argv/status/stdout/stderr for every negative fixture."""
    repo = Path(__file__).resolve().parents[1]
    argv = [sys.executable, "-B", "-s", str(repo / "verify_prototype_outputs.py"),
            "--reference", str(root / "main"), "--repeat", str(root / "repeat"),
            "--reload", str(root / "reload"), "--output", str(root / "cli-report.json")]
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    result = subprocess.run(argv, cwd=repo, text=True, capture_output=True, timeout=120)
    record = dict(argv=argv, cwd=str(repo), start_utc=start,
                  end_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  exit=result.returncode, stdout=result.stdout, stderr=result.stderr)
    with (root / "cli-execution.json").open("x") as stream:
        json.dump(record, stream, indent=2)
    return result, json.loads((root / "cli-report.json").read_text())


@pytest.mark.parametrize("case", ["empty_spec", "summary_string", "per_seed_string"])
def test_three_original_failures(valid, tmp_path, case):
    copies(valid, tmp_path)
    if case == "empty_spec":
        mutate(tmp_path, "campaigns.json", None, "spec", {})
        diagnostic = "spec: missing required fields"
    elif case == "summary_string":
        mutate(tmp_path, "summary.json", None, "success_mean", "not-a-number")
        diagnostic = "summary.json.success.*finite numeric"
    else:
        mutate(tmp_path, "per_seed.csv", None, "success", "not-a-number")
        diagnostic = "per_seed.csv.success.*finite numeric"
    rejected(tmp_path, diagnostic)


@pytest.mark.parametrize("key,value,diagnostic", [
    ("target_amount", "23460.31", "spec.target_amount.*finite numeric"),
    ("target_amount", True, "spec.target_amount.*finite numeric"),
    ("target_amount", 0, "spec.target_amount.*positive"),
    ("target_amount", -1, "spec.target_amount.*range"),
    ("target_amount", float("nan"), "Non-finite JSON"),
    ("target_amount", float("inf"), "Non-finite JSON"),
    ("campaign_id", 101, "spec.campaign_id"),
    ("campaign_id", "wrong", "spec.campaign_id"),
    ("family", [], "spec.family"),
    ("family", "unsupported", "spec.family"),
    ("fraud_type", "unknown", "spec.fraud_type"),
    ("vpa_strategy", {}, "spec.vpa_strategy"),
    ("start_time", None, "spec.start_time"),
    ("start_time", "not-a-date", "spec.start_time"),
    ("start_time", "2026-01-05T12:00:00+00:00", "spec.start_time"),
    ("policy_seed", True, "spec.policy_seed"),
    ("timer_seed", "101", "spec.timer_seed"),
    ("vpa_seed", 1.5, "spec.vpa_seed"),
    ("is_fraud", 1, "spec.is_fraud"),
])
def test_malformed_spec(valid, tmp_path, key, value, diagnostic):
    copies(valid, tmp_path)
    mutate(tmp_path, "campaigns.json", "spec", key, value)
    rejected(tmp_path, diagnostic)


@pytest.mark.parametrize("key", [
    "campaign_id", "family", "fraud_type", "target_amount", "vpa_strategy",
    "start_time", "policy_seed", "timer_seed", "vpa_seed", "is_fraud"])
def test_missing_spec_fields(valid, tmp_path, key):
    copies(valid, tmp_path)
    mutate(tmp_path, "campaigns.json", "spec", key, None, remove=True)
    rejected(tmp_path, f"spec: missing required fields.*{key}")


@pytest.mark.parametrize("filename,key", [
    ("summary.json", "success_mean"), ("summary.csv", "success_mean"),
    ("per_seed.csv", "success"), ("summary.json", "exposure_mean"),
    ("summary.csv", "exposure_mean"), ("per_seed.csv", "exposure")])
@pytest.mark.parametrize("value", ["not-a-number", "NaN", "Infinity", "-Infinity"])
def test_nonnumeric_and_nonfinite_metrics(valid, tmp_path, filename, key, value):
    copies(valid, tmp_path)
    mutate(tmp_path, filename, None, key, value)
    rejected(tmp_path, "finite numeric")


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_raw_nonfinite_json(valid, tmp_path, value):
    copies(valid, tmp_path)
    mutate(tmp_path, "summary.json", None, "success_mean", value)
    rejected(tmp_path, "Non-finite JSON")


@pytest.mark.parametrize("key", METRICS)
@pytest.mark.parametrize("filename", ["summary.json", "summary.csv", "per_seed.csv"])
def test_missing_numeric_fields(valid, tmp_path, filename, key):
    copies(valid, tmp_path)
    field = key if filename == "per_seed.csv" else key + "_mean"
    mutate(tmp_path, filename, None, field, None, remove=True)
    rejected(tmp_path, "missing required metric fields|column schema")


@pytest.mark.parametrize("filename,key,value", [
    ("summary.json", "success_mean", 1.01),
    ("summary.json", "success_mean", -0.01),
    ("summary.json", "success_mean", True),
    ("summary.json", "attempted_mean", 4),
    ("summary.json", "exposure_mean", -1),
    ("summary.json", "detection_seconds_observed", -1),
    ("summary.json", "detection_seconds_observed", 3),
    ("summary.json", "detection_seconds_mean_observed", -1),
    ("summary.json", "campaigns", 1),
    ("summary.json", "seeds", True),
    ("summary.csv", "success_mean", 1.01),
    ("summary.csv", "allowed_mean", -1),
    ("summary.csv", "campaigns", 1.5),
    ("summary.csv", "seeds", 2),
    ("per_seed.csv", "success", -0.01),
    ("per_seed.csv", "success", 1.01),
    ("per_seed.csv", "attempted", 4),
    ("per_seed.csv", "exposure", -1),
    ("per_seed.csv", "n", 1.5),
    ("per_seed.csv", "n", 1),
    ("per_seed.csv", "seed", 999),
])
def test_ranges_and_counts(valid, tmp_path, filename, key, value):
    copies(valid, tmp_path)
    mutate(tmp_path, filename, None, key, value)
    rejected(tmp_path, "range|numeric|count|sample|integer|identities")


@pytest.mark.parametrize("key,value", [
    ("success_seed_sd", -1), ("exposure_seed_sd", "not-a-number"),
    ("success_seed_sd", 1.01), ("success_seed_sd", None),
])
def test_multiseed_sd(valid_two_seeds, tmp_path, key, value):
    copies(valid_two_seeds, tmp_path)
    mutate(tmp_path, "summary.json", None, key, value)
    rejected(tmp_path, "range|finite numeric")


@pytest.mark.parametrize("source", ["valid", "valid_two_seeds"])
def test_valid_fresh_content_and_equality(request, source, tmp_path):
    root = request.getfixturevalue(source)
    result = verify(root / "main", root / "repeat", root / "reload")
    assert result["evidence_complete"] is True
    assert result["byte_equal"] is True
    assert result["scientific_validity"] is False
    assert result["passed"] is True
    summary = json.loads((root / "main/summary.json").read_text())
    if source == "valid":
        assert all(row["success_seed_sd"] is None for row in summary)
    else:
        assert all(isinstance(row["success_seed_sd"], (int, float)) for row in summary)
    assert any(row["blocked_mean"] == 0 for row in summary)
    assert any(row["intervention_seconds_mean_observed"] is None for row in summary)
    copies(root, tmp_path)
    result, cli_report = checker_cli(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert cli_report["evidence_complete"] is True and cli_report["byte_equal"] is True


@pytest.mark.parametrize("value", [
    "2026-01-05", "not-a-timestamp", "2026-01-05T12:00:00+00:00",
    "2026-01-05T12:00:00Z", "2026-02-30T12:00:00",
    "2026-01-05T12:00", "2026-01-05T",
])
def test_complete_naive_timestamp_cli(valid, tmp_path, value):
    copies(valid, tmp_path)
    mutate(tmp_path, "campaigns.json", "spec", "start_time", value)
    rejected(tmp_path, r"spec.start_time: expected YYYY-MM-DDTHH:MM:SS.*naive simulated UTC")


@pytest.mark.parametrize("fractional", [False, True])
def test_observed_timestamp_and_optional_fraction_cli(valid, tmp_path, fractional):
    copies(valid, tmp_path)
    observed = json.loads((valid / "main/campaigns.json").read_text())[0]["spec"]["start_time"]
    if fractional:
        value = datetime.datetime.fromisoformat(observed).replace(microsecond=123456).isoformat()
        mutate(tmp_path, "campaigns.json", "spec", "start_time", value)
    result, report = checker_cli(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert report["evidence_complete"] is True and report["byte_equal"] is True
    assert report["scientific_validity"] is False


@pytest.mark.parametrize("value", [None, 123, True, []],
                         ids=["null", "integer", "boolean", "list"])
def test_start_time_wrong_type_cli(valid, tmp_path, value):
    copies(valid, tmp_path)
    mutate(tmp_path, "campaigns.json", "spec", "start_time", value)
    rejected(tmp_path, r"spec.start_time: expected nonempty string")
    report = json.loads((tmp_path / "cli-report.json").read_text())
    execution = json.loads((tmp_path / "cli-execution.json").read_text())
    assert execution["exit"] == 1
    assert report["error"] == "spec.start_time: expected nonempty string"
    assert report["evidence_complete"] is False
    assert "Traceback" not in execution["stderr"]
    assert "TypeError" not in execution["stderr"] + report["error"]
