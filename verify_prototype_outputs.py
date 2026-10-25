"""Recompute repeat/reload equality evidence; comparisons are byte-for-byte."""
import argparse
import hashlib
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--reference", type=Path, required=True)
parser.add_argument("--repeat", type=Path, required=True)
parser.add_argument("--reload", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
report = {"repeat": {}, "reload": {}, "policies": {}, "source_identity": {}}
common = ["campaigns.json", "summary.json", "summary.csv", "per_seed.csv",
          "transactions.csv", "comparison.svg"]
for name in common + ["learning.csv", "learning.svg", "manifest.json"]:
    a, b = (args.reference / name).read_bytes(), (args.repeat / name).read_bytes()
    report["repeat"][name] = {"equal": a == b, "sha256": hashlib.sha256(a).hexdigest()}
for name in common:
    a, b = (args.reference / name).read_bytes(), (args.reload / name).read_bytes()
    report["reload"][name] = {"equal": a == b, "sha256": hashlib.sha256(a).hexdigest()}
for path in args.reference.glob("q_*.json"):
    a, b = path.read_bytes(), (args.repeat / path.name).read_bytes()
    report["policies"][path.name] = {"equal": a == b, "sha256": hashlib.sha256(a).hexdigest()}
manifest = json.loads((args.reference / "manifest.json").read_text())
root = Path(__file__).resolve().parent
for name, expected in manifest["source_sha256"].items():
    report["source_identity"][name] = {
        "equal": hashlib.sha256((root / name).read_bytes()).hexdigest() == expected}
report["passed"] = all(entry["equal"] for group in
                       ("repeat", "reload", "policies", "source_identity")
                       for entry in report[group].values())
with args.output.open("x") as stream:
    json.dump(report, stream, indent=2, sort_keys=True)
print(json.dumps({"passed": report["passed"],
                  "comparisons": {k: len(report[k]) for k in
                                  ("repeat", "reload", "policies", "source_identity")}}))
raise SystemExit(0 if report["passed"] else 1)
