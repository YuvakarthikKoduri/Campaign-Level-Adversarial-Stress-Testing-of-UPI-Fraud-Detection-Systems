# Prototype presentation and demonstration

The project is a synthetic campaign stress-testing prototype, not a deployed UPI
system. It compares static, feedback-driven rule and learned tabular policies
against the existing XGBoost and Random Forest detectors, with transaction-level
decisions and reproducible campaign metrics.

## Suggested five-part presentation

- **Question:** How do campaign outcomes change when an attacker can react to
  feedback rather than follow a preset trajectory? Distinguish attacker success
  from detector quality and gross flow from real victim loss.
- **Architecture:** Show `architecture.svg`. All policies use the same existing
  executor/environment; the RL agent receives public decisions and its own
  progress, not detector internals. Explain training versus frozen evaluation.
- **Method:** Show the state/action/reward definition in `PROTOTYPE_GUIDE.md`.
  The Q table learns over training episodes; an untrained identical-action-space
  control helps identify what learning changes.
- **Results:** Show `comparison-final/comparison.svg`, `learning.svg` and
  `per_seed.csv`. Use the completion-report table for three-seed variability.
  RL improved over its untrained known-workload control, but did not universally
  beat existing actors; Random Forest known-workload RL success was 98.6%
  versus 100% for both legacy actors.
- **Evidence and limitations:** Show the final 201-test JUnit/log result,
  byte-identical repeat and policy-reload verification. State the synthetic-data,
  nominal detector-unseen provenance, small seed count, action-space and exposure
  limitations. Gate C remains separately held.

## Short live demonstration

After setup from `PROTOTYPE_GUIDE.md`, run this from the extracted project root.
The output directory must not already exist; use a new name for each run.

```sh
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONHASHSEED=17 PYTHONDONTWRITEBYTECODE=1 TZ=UTC
python -B -s run_prototype.py --detector both --attacker all --seeds 101 \
  --episodes 60 --campaigns 6 --max-steps 30 --output reviewer-demo
```

Open `reviewer-demo/comparison.svg` and `learning.svg`. Inspect `summary.csv`
for outcomes, `per_seed.csv` for the seed-level table and `transactions.csv`
for decisions. Inspect a transaction's `rl_transition` in `campaigns.json` to
show the actual state, selected action, reward and terminal flag.

Show a saved `q_xgboost_101.json`: it contains learned values and the checked
detector/seed/threshold/horizon metadata. Re-evaluate without retraining:

```sh
python -B -s run_prototype.py --detector both --attacker all --seeds 101 \
  --episodes 60 --campaigns 6 --max-steps 30 --policy-dir reviewer-demo \
  --output reviewer-reload
cmp reviewer-demo/campaigns.json reviewer-reload/campaigns.json
```

The reported full experiment uses 300 training episodes, three seeds and 24
campaigns per kind, not this smaller live demo. Do not present the live sample
as the complete evaluation dataset or its outcomes as guaranteed on all systems.

## Main experiment in one command

After dependency setup and environment exports, this is the full reported
configuration. This command trains and evaluates; no separate preparatory
workflow is needed.

```sh
python -B -s run_prototype.py --detector both --attacker all \
  --seeds 101 202 303 --episodes 300 --campaigns 24 --max-steps 30 \
  --output reviewer-full
```
