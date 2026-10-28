"""Read-only arithmetic for historical prototype records; never runs experiments."""
import argparse
from collections import Counter
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path

def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, default=root/"prototype_evidence/comparison-final")
    parser.add_argument("--output", required=True, type=Path, help="Fresh JSON path, never overwritten")
    args = parser.parse_args()
    p = args.records
    records = json.loads((p/"campaigns.json").read_text())
    flat = [t for r in records for t in r["transactions"]]
    transactions = list(csv.DictReader((p/"transactions.csv").open()))
    summary = list(csv.DictReader((p/"summary.csv").open()))
    checks = 0
    def check(value):
        nonlocal checks
        checks += 1
        if not value:
            raise ValueError("Historical record arithmetic mismatch at check "+str(checks))
    check(len(flat) == len(transactions))
    check(len(records) == sum(int(r["campaigns"]) for r in summary))
    check(Counter(t["decision"] for t in flat) == Counter(t["decision"] for t in transactions))
    gross = sum(Decimal(str(t["amount_transferred"])) for t in flat)
    check(gross == sum(Decimal(t["amount_transferred"]) for t in transactions))
    for r in records:
        check(r["metrics"]["attempted"] == len(r["transactions"]))
        check(sum(r["metrics"][k] for k in ("allowed","flagged","blocked")) == len(r["transactions"]))
        check(abs(Decimal(str(r["metrics"]["exposure"]))-
                  sum(Decimal(str(t["amount_transferred"])) for t in r["transactions"])) < Decimal(".000001"))
    for row in summary:
        group = [r for r in records if all(r[k] == row[k] for k in ("detector","kind","attacker"))]
        check(len(group) == int(row["campaigns"]))
        check(abs(sum(r["metrics"]["success"] for r in group)/len(group)-float(row["success_mean"])) < 1e-12)
        check(len({r["seed"] for r in group}) == int(row["seeds"]))
    result = dict(
        experiment="historical academic-prototype-v1 / comparison-final",
        campaigns=len(records), completed=sum(r["metrics"]["success"] for r in records),
        transactions=len(flat), decisions=dict(Counter(t["decision"] for t in flat)),
        gross_simulated_debit_inr=str(gross), checks=checks,
        source_sha256={n: hashlib.sha256((p/n).read_bytes()).hexdigest()
                       for n in ("campaigns.json","transactions.csv","summary.csv","config.json")},
        limitation="Arithmetic consistency only; not scientific validation or the later corrected study.")
    with args.output.open("x") as stream:
        json.dump(result,stream,indent=2)
        stream.write("\n")
    print(json.dumps(result,indent=2))

if __name__ == "__main__":
    main()
