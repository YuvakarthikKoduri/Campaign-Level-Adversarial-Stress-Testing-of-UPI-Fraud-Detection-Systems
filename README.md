# UPI Fraud Stress Lab

UPI Fraud Stress Lab is a Python research prototype for asking a practical question: **can a simulated attack campaign reach its transfer target before a fraud detector stops it?** It connects campaign generation, attacker decisions, a synthetic account ledger and two saved machine-learning detectors, then records the entire sequence for inspection.

This page describes **`prototype/rl-academic-complete`**, the selected final project branch for the faculty presentation, whose research-code baseline is `92a12966ec49fd6dcd147fd4d7411382715bc729`. It is a command-line prototype, not the separate corrected dashboard and mechanism-holdout pilot; final branch selection and documentation updates do not backport those fixes or certify scientific validity.

> This is a synthetic research environment. Results do not establish real-world UPI fraud-detection effectiveness, actual victim losses or money saved. Gate C remains HOLD.

## The lecturer pitch

Most detector summaries describe individual transactions. Our prototype instead runs a sequence: an attacker proposes transfers, the detector allows, flags or blocks them, and the simulator checks whether the campaign reaches its target. The useful engineering contribution is an inspectable connection between attacker behavior, intervention timing and simulated ledger effects, with saved policies and reproducible raw outputs. It is not a new detector algorithm, a first-ever learning attack or proof of real-world fraud prevention.

The [eight-slide presentation](research/review_materials/UPI_PROTOTYPE_FACULTY_8_SLIDES.pptx) is editable in PowerPoint. Its [PDF preview](research/review_materials/UPI_PROTOTYPE_FACULTY_8_SLIDES.pdf) and [handover](docs/PROTOTYPE_FACULTY_HANDOVER.md) explain this exact branch rather than silently mixing later experiments into it.

## What is implemented here?

| Component | Actual prototype behavior |
|---|---|
| Detectors | Saved XGBoost and Random Forest models, reused for inference |
| Workloads | HIGH_VALUE_BURST, SLOW_DRAIN, GRADUAL_ESCALATION and BENEFICIARY_HOPPING |
| Static attacker | Family-specific behavior without detector-feedback adaptation |
| Rule-adaptive attacker | Hand-written rules that respond to prior outcomes |
| Trained RL attacker | Tabular Q-learning, with training before evaluation |
| Zero-Q control | The same RL action vocabulary without learned Q values; CLI name `untrained_rl` |
| Campaign execution | Targets, synthetic balances, pacing, ALLOW/FLAG/BLOCK decisions and stopping reasons |
| Evidence | Campaign JSON, transaction CSV, summary tables, Q checkpoints, manifests and SVG plots |
| Not on this branch | Local dashboard, label-blind RL arm, later matched pilot and later remediation fixes |

RL means reinforcement learning. Here its small table has at most 64 state keys and 16 amount/pacing/recipient combinations; it is not a neural-network model or a claim of optimal learning.

```text
Campaign workload -> Attacker action -> Synthetic ledger + detector -> Recorded outcome
                            ^                       |
                            +---- public feedback --+
```

The [prototype guide](docs/PROTOTYPE_GUIDE.md) contains the reward, state/action definition, stopping rules and output schema. Its historical claims and the old completion report must be interpreted with the version limitations below.

## Install and run from a terminal

Use Python 3.11 on Linux or WSL2. Native Windows execution is not established by the checks reported here; on Windows, open an Ubuntu/WSL terminal and follow these commands there.

```bash
git clone --branch prototype/rl-academic-complete --single-branch \
  https://github.com/YuvakarthikKoduri/Campaign-Level-Adversarial-Stress-Testing-of-UPI-Fraud-Detection-Systems.git
cd Campaign-Level-Adversarial-Stress-Testing-of-UPI-Fraud-Detection-Systems

python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-milestone1.lock

export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONHASHSEED=17 PYTHONDONTWRITEBYTECODE=1 TZ=UTC

python -B -s run_prototype.py \
  --detector both --attacker all --seeds 101 \
  --episodes 2 --campaigns 1 \
  --output demo-faculty-01
```

This deliberately small demonstration evaluates 16 campaigns: two detectors, two workload groups and four attacker controls, with one campaign per cell. It trains two RL episodes per detector; it does not reproduce the retained full-study results and does not run Gate C.

Use a **new output directory every time**. The program refuses to overwrite an existing run, so use `demo-faculty-02` for another attempt rather than deleting historical evidence.

The short main/reload commands were newly exercised in an isolated checkout using the existing compatible Python environment. That is a verified execution path, not a new clean-install certification of every operating system.

## What to open after a run

| File in `demo-faculty-01/` | What it tells you |
|---|---|
| `summary.csv` / `summary.json` | Completion and other metrics by detector, workload group and strategy |
| `campaigns.json` | Workload specifications, target, stopping reason and transaction-level records |
| `transactions.csv` | Evaluated decisions and amounts in a flat table |
| `comparison.svg` | Recorded comparison plots; open in a browser |
| `learning.csv` / `learning.svg` | Training diagnostics, not a guarantee of better evaluation performance |
| `q_*.json` | Saved policy state and configuration |
| `manifest.json` / `config.json` | Model identifiers, software/configuration details and recorded update counts |

Start with `summary.csv`, then pick a campaign in `campaigns.json` and follow its transaction rows. A FLAG can still transfer money in the simulator; a BLOCK stops the campaign.

## Supported choices and checkpoint evaluation

Run `python -B -s run_prototype.py --help` to inspect the actual CLI. Supported detector choices are `both`, `xgboost` and `random_forest`; attacker choices are `all`, `static`, `adaptive`, `rl` and `untrained_rl`.

```bash
# Evaluate the saved policies without new training.
# Keep seed, episode/configuration flags, horizon and thresholds consistent.
python -B -s run_prototype.py \
  --detector both --attacker all --seeds 101 \
  --episodes 2 --campaigns 1 \
  --policy-dir demo-faculty-01 --output demo-faculty-reload-01

# Run just the trained policy with one detector, in a new directory.
python -B -s run_prototype.py \
  --detector xgboost --attacker rl --seeds 101 \
  --episodes 2 --campaigns 1 --output demo-faculty-rl-01

# Run the targeted existing RL regression selection.
python -B -s -m pytest tests/test_prototype_rl.py -q
```

Checkpoint reload repeats evaluation with a matching policy identity. The legacy reload manifest carries the original training update count; this inherited count is not evidence that reload trained again, and zero recorded evaluation updates does not by itself prove complete Q-table immutability in this older implementation.

## Recorded results, with the version made explicit

The preserved source for this table is `prototype_evidence/comparison-final/` on this branch. A new read-only calculation checked the campaign JSON against transaction and summary files; it did not rerun the full experiment.

```bash
# Recalculate retained records without training or running a new experiment.
python -B scripts/recalculate_prototype_snapshot.py --output reviewer-prototype-check.json
```

| Historical prototype measure | Recalculated value |
|---|---:|
| Evaluated campaigns | 1,152 |
| Completed campaigns | 1,077 |
| Evaluated transactions | 4,189 |
| ALLOW / FLAG / BLOCK | 3,229 / 885 / 75 |
| Independent evaluation seeds | 3: 101, 202, 303 |
| Gross simulated source debit | INR 29,196,913.14 |

Completion means reaching the declared transfer target before termination. Evaluated transactions are the recorded ALLOW/FLAG/BLOCK decisions; gross debit sums `amount_transferred` and includes FLAG transfers, not actual victim loss.

These are **historical observations from the older implementation, not final validated scientific estimates**. In particular, do not substitute the later corrected legacy count of 4,161 transactions or the later pilot's 7,200 campaigns into this branch's table.

The separate review branch contains decimal-money, evaluation-state and evidence-checking repairs, a matched pilot and its adverse benign-shift finding. Those are supplemental, version-specific materials, not the selected final branch for this presentation; do not interpret this README update as repairing this branch's research engine.

## Dashboard and current IEEE report

The [complete review branch](https://github.com/YuvakarthikKoduri/Campaign-Level-Adversarial-Stress-Testing-of-UPI-Fraud-Detection-Systems/tree/review/academic-dashboard-paper-v1) contains the local dashboard, corrected evidence, literature matrix and IEEE paper. It is a different implementation/evidence version, not an optional dashboard dependency you can start from this checkout.

To use the dashboard, make a **separate clone** with `--branch review/academic-dashboard-paper-v1`, follow that branch's README and run `python -B -s run_dashboard.py --port 8765` from its activated environment. Do not copy files between clones or expect `run_dashboard.py` to exist on this prototype branch.

The [IEEE PDF](https://github.com/YuvakarthikKoduri/Campaign-Level-Adversarial-Stress-Testing-of-UPI-Fraud-Detection-Systems/blob/review/academic-dashboard-paper-v1/research/paper/main.pdf) and [LaTeX source/build instructions](https://github.com/YuvakarthikKoduri/Campaign-Level-Adversarial-Stress-Testing-of-UPI-Fraud-Detection-Systems/tree/review/academic-dashboard-paper-v1/research/paper) cover the later corrected study and pilot. The draft is AI-assisted; no skill or formatting step makes that text human-authored or establishes a zero AI-content score.

Both AI-content and similarity requirements remain **PENDING EXTERNAL VERIFICATION** using the university-approved tools on the exact final document. See [the report recheck and human-review steps](docs/IEEE_REPORT_STATUS.md); no measured score or threshold compliance is claimed.

## Limitations and troubleshooting

- **Unverified detector holdout:** Three workload families were excluded from RL training, not demonstrably from historical detector training. “Unknown” in older output files is a workload-group label, not proof of detector-unseen fraud.
- **Confounded comparisons:** Action vocabularies, pacing, final-transfer clipping and offline training costs differ across legacy policies. Completion differences do not establish a causal adaptation advantage or universal RL superiority.
- **Older evaluation implementation:** Later audits tightened frozen-policy equality, money handling and schema validation. A passing older suite is not proof that those later defects are absent here.
- **No dashboard on this branch:** Use the separately identified review branch rather than trying an unsupported startup command.
- **Model warning:** The old XGBoost pickle can emit a version/portability warning. Use the pinned environment and only trusted project model artifacts; never load an arbitrary pickle.
- **Import or model-file errors:** Run commands from the repository root after activating the environment. Do not move the runner away from `src/`, `models/` or `data/`.
- **Output already exists:** Pick a fresh output path instead of overwriting evidence.
- **Historical AUC/test claims:** Old reports and Git history are preserved, but their AUC values, completion percentages and counts are not adopted as current acceptance evidence here.

Scientific validity extends only as far as the evidence and stated assumptions. This is an exploratory academic prototype, not a production detector, a real payment system or an authorized Gate C workflow.
