# UPI Fraud Stress Lab

UPI Fraud Stress Lab is a working research application that asks: **can a simulated attack campaign reach its transfer target before a fraud detector stops it?** We built a Python simulation engine and an interactive dashboard to run that experiment, compare attacker strategies, inspect individual decisions and reproduce the recorded findings.

This is a synthetic, UPI-inspired academic project, not a live payment system. It does not connect to banks, NPCI or real accounts, and its results do not establish real-world UPI fraud-detection effectiveness.

## The project in 30 seconds

> Our project moves the evaluation question from “Was this transaction classified correctly?” to “What happened across the whole attack?” We simulate sequences of transfers against XGBoost and Random Forest detectors, compare predefined, feedback-driven and learned attacker policies, and measure target completion, intervention timing and simulated debit. The contribution is a reproducible research workstation with controlled comparisons, traceable records and a dashboard that can execute the experiments. Importantly, it also exposes a failure: legitimate gradual-escalation lookalikes are frequently blocked, showing why a held-out fraud pattern alone is not evidence of a reliable detector.

For a faculty review, start with the problem and findings below, then use the [live demonstration guide](docs/REVIEW_DEMONSTRATION.md). The [paper](research/paper/main.pdf), [editable slides](research/review_materials/review_deck.pptx) and [faculty Q&A](research/review_materials/questions_and_answers.md) provide the supporting academic material.

## Why evaluate a campaign instead of only a transaction?

A transaction-level score answers a question about one payment proposal. It does not, by itself, describe whether a sequence reaches its target, how soon intervention happens or how the attacker responds to previous decisions.

| Evaluation question | What the campaign view adds |
|---|---|
| Is a transaction allowed, flagged or blocked? | The complete decision sequence and the point at which the campaign stops |
| How does a detector score an example? | Whether the simulated attacker reaches a predefined target under time and action limits |
| What changes when an attacker receives feedback? | Comparisons between predefined, rule-adaptive and learned policies under common online constraints |
| Does a suspicious pattern trigger detection? | A separate check of whether legitimate lookalikes are also blocked |

These are complementary questions, not a claim that sequential or adversarial evaluation is new. Our [literature comparison](research/literature_review/comparison_matrix.csv) distinguishes existing research from the system implemented here.

## What we actually built

- **Campaign simulator:** a synthetic ledger executes transfer proposals, records decisions and stops campaigns according to their target, intervention and resource limits. Each campaign retains its transaction sequence rather than only a final score.
- **Two detector baselines:** XGBoost and Random Forest provide the decisions against which attacker policies are evaluated. The legacy study uses preserved model artifacts; the separate matched pilot fits models from registered synthetic inputs.
- **Attacker comparisons:** the pilot evaluates static, rule-adaptive, trained RL, explicit-label-blind trained RL and zero-Q control policies. The label-blind arm hides explicit decisions but is not completely feedback-free, because its reward still contains outcome information.
- **Research dashboard:** eleven sections support real execution, terminal logs, results filtering, detector/attacker comparisons, campaign drill-down, data/model inspection, tests and exports. It is a local application, not a screenshot-only prototype.
- **Reproducibility tools:** saved configurations, seeds, hashes, checkpoints, raw records and independent reconstruction connect reported numbers to the execution that produced them.

The legacy simulator implements four campaign families. The newer matched pilot intentionally evaluates only two; it does not claim matched evidence for all four.

| Campaign family | Behavior represented | Legacy simulator | Matched pilot |
|---|---|---|---|
| `HIGH_VALUE_BURST` | A burst of relatively large transfer proposals | Supported | Evaluated; allowed in development |
| `SLOW_DRAIN` | Smaller transfers spread over time | Supported | Not evaluated |
| `GRADUAL_ESCALATION` | Transfer amounts increase through the campaign | Supported | Evaluated; declared mechanism excluded from registered detector-development data |
| `BENEFICIARY_HOPPING` | Transfers vary the beneficiary | Supported | Not evaluated |

![Implemented system architecture](docs/images/architecture.svg)

The dashboard sends validated configurations to a fixed-command execution adapter, which runs the existing Python engines. Results parsing, visualization and independent verification remain separate from the simulator; see the [architecture and source map](docs/ARCHITECTURE.md).

## What makes this project distinctive?

The defensible contribution is the **implemented combination of campaign evaluation, controlled synthetic experiments and inspectable evidence**, rather than a claim to have invented fraud detection or reinforcement learning. The [novelty analysis](research/literature_review/NOVELTY_ANALYSIS.md) explains the overlap with prior work and the limits of this contribution.

| Project contribution | Why it is useful in a review | Where to inspect it |
|---|---|---|
| Campaign-level outcomes | Shows target completion and intervention across a sequence, not just isolated classifications | [Metric definitions](docs/METRICS_AND_DEFINITIONS.md) and Campaign Analysis in the dashboard |
| Five matched pilot controls | Makes predefined, feedback-driven and learned policies comparable on legal actions and online limits; offline training costs still differ | [Experimental methodology](docs/EXPERIMENT_METHODOLOGY.md) |
| Registered synthetic mechanism exclusion | Makes the narrow holdout claim inspectable through development membership, source identities and artifacts | [Data and models](docs/DATA_AND_MODELS.md) |
| Legitimate mechanism-shift controls | Tests whether legitimate behavior resembling the evaluated attack mechanism is also blocked | [Benign-control results](results/comparison_tables/benign_controls.csv) |
| Independent reconstruction | Checks reported metrics and recorded learning updates instead of relying only on a summary table | [Verification report](docs/VERIFICATION_REPORT.md) |
| A working research interface | Lets a lecturer run a short experiment, follow its logs and inspect the evidence without manually reading JSON | [Dashboard guide](docs/DASHBOARD_GUIDE.md) |

Prior research already includes sequential fraud models, financial simulators and RL-based evasion. We do not claim that this is the first such system, a new RL algorithm or a superior fraud detector; the [eleven-work literature matrix](research/literature_review/comparison_matrix.csv) supports a more precise comparison.

## What the experiments found

The table below describes the **retained full mechanism-holdout pilot**, not a newly launched demonstration. Its attack campaigns span both evaluated mechanisms, both detectors and five attacker controls across nine independent blocks.

| Measurement | Verified result | Meaning |
|---|---:|---|
| Independent blocks / detector fits | 9 / 18 | Independent pilot blocks, with two detector fits per block |
| Attack campaigns attempted | 7,200 | Evaluated simulated attacks, excluding separate benign-control episodes |
| Attack campaigns completed | 3,539 / 7,200 (49.153%) | The attacker reached its defined target; this is not detector accuracy |
| Transactions evaluated | 28,895 | Scored proposals, including those blocked |
| ALLOW / FLAG / BLOCK | 24,634 / 600 / 3,661 | Recorded simulator decisions; a FLAG can still permit a transfer |
| Gross simulated source debit | INR 192,300,996.32 | Recorded simulated debit, not actual victim loss or money saved |

### Comparing attacker strategies

On the declared held-out gradual-escalation mechanism, completion varied substantially by detector and policy. Each cell below contains 360 evaluated campaigns across nine blocks; these are exploratory observations, not confirmatory superiority claims.

| Detector | Static | Rule-adaptive | Trained RL | Label-blind RL | Zero-Q |
|---|---:|---:|---:|---:|---:|
| XGBoost | 1.667% | 75.278% | 43.333% | 42.222% | 50.833% |
| Random Forest | 71.111% | 100.000% | 91.944% | 89.722% | 85.278% |

Rule adaptation improves observed completion in this particular gradual-escalation comparison, but trained RL does not consistently outperform its controls. The [complete results](results/results_summary.csv) include the allowed high-value-burst mechanism, block variability and intervention measures; the [paired contrasts](results/comparison_tables/paired_contrasts.csv) report exploratory, unadjusted uncertainty.

### The most important finding is also a limitation

Both detectors had zero observed BLOCK among 3,600 ordinary-benign test episodes each. However, when legitimate episodes resembled the gradual-escalation mechanism, XGBoost blocked **1,738/3,600 (48.278%)**, and Random Forest blocked **461/3,600 (12.806%)**.

![Observed false blocking of legitimate gradual-escalation mimics](research/paper/figures/benign_shift.svg)

This is an adverse result, not something to hide: excluding a declared mechanism from synthetic development data does not guarantee useful fraud discrimination. Zero observed ordinary-benign blocking is also not a guarantee of zero false blocking in a real population; see the [results interpretation](docs/RESULTS_AND_INTERPRETATION.md).

The corrected legacy study is separate: it contains 1,152 campaigns and 4,161 transactions across three seeds, with different comparison conditions. Its [results table](results/comparison_tables/legacy_separate.csv) must not be pooled with the pilot, and its known-workload results do not establish an “adaptation paradox.”

## What a lecturer can see in the dashboard

The application turns the research workflow into a live demonstration. It can execute supported programs, not merely display pre-entered summary numbers.

![Actual running research dashboard](docs/images/dashboard.png)

This screenshot was captured from the running integration checkout before its final review commits and later UI checks. When started locally, the top bar obtains the actual checkout identity and execution status rather than hard-coding the screenshot's values.

1. Select retained `pilot-main` and explain the campaign, decision and debit metrics.
2. Launch a short real experiment from **Run Experiments**, after reviewing its generated command.
3. Watch stdout/stderr, execution status, elapsed time and exit code in **Terminal & Logs**.
4. Filter **Results Explorer**, compare compatible detector/attacker cells and open the deterministic result explanation.
5. Inspect a campaign transaction by transaction, including proposed/transferred amounts, simulated timing and termination.
6. Export CSV, Markdown and SVG, then follow the underlying records and model/provenance links.

All eleven sections are documented in the [dashboard guide](docs/DASHBOARD_GUIDE.md). Execution uses allowlisted commands and validated arguments, with fresh output directories, duplicate-job protection and safe cancellation; there is no unrestricted shell or Git/Gate C execution endpoint.

## Run the project from a terminal

Linux or WSL2 with Python 3.11 is the verified target. Use a Git clone rather than a source-only copy, because the legacy runner records Git context; native Windows, macOS and other dependency sets are not claimed as verified.

### Install and open the dashboard

```sh
git clone --branch review/academic-dashboard-paper-v1 \
  https://github.com/YuvakarthikKoduri/Campaign-Level-Adversarial-Stress-Testing-of-UPI-Fraud-Detection-Systems.git
cd Campaign-Level-Adversarial-Stress-Testing-of-UPI-Fraud-Detection-Systems

python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-milestone1.lock

# Restore preserved evidence; this does not train models or run experiments.
python -B scripts/restore_evidence.py

# Start the local research application.
python -B -s run_dashboard.py --port 8765
```

Open [the local dashboard](http://127.0.0.1:8765), leaving the server terminal running. The dashboard is single-user and localhost-only; do not expose it through a public bind address or proxy.

The restorer checks the bundled archive and reconstructs 715 exact preserved files under `.local/retained/`. New dashboard jobs and logs are stored separately under `.local/dashboard-state/`; [installation](docs/INSTALLATION.md) and [artifact handling](results/artifacts/README.md) explain the environment and checksums.

### Run a short experiment without the dashboard

Use a second activated terminal in the repository root, or stop the dashboard before continuing. These are deliberately small demonstrations, not reproductions of the full 7,200-campaign study.

```sh
# Legacy demonstration: both detectors and all supported attacker strategies.
python -B -s run_prototype.py \
  --detector both --attacker all --seeds 101 \
  --episodes 6 --campaigns 2 \
  --output .local/faculty-legacy-main

# Matched pilot: one block, both detectors, five controls, two mechanisms.
python -B -s -m src.experiments.mechanism_pilot \
  --blocks 1 --episodes 2 --contexts 2 --seed-base 71000 \
  --output .local/faculty-pilot-main
```

In the legacy command, `--episodes` is policy-training episodes per detector/seed, and `--campaigns` is evaluation campaigns per family/attacker/detector/seed. In the pilot, `--episodes` controls learned-policy training and `--contexts` controls paired evaluation contexts per mechanism/block; the pilot runs its fixed detector/control bundle rather than unsupported individual-arm selections.

Outputs are written to the named directories, and existing directories are refused rather than overwritten. Choose a fresh output name for another attempt; preserve failed or completed runs instead of deleting them to obtain a clean result.

### Demonstrate saving, repeating and reloading

The scripted faculty fallback runs both engines' short main/repeat/checkpoint-reload workflows and their checkers. It preserves the command journal, logs and outputs under `.local/review-demo/` and refuses that directory if it already exists.

```sh
python -B scripts/review_smoke.py
```

For a legacy checkpoint-only evaluation after the direct demonstration above, the following reuses the saved policies without policy training. Keep the detector, seed and campaign settings consistent with their source run.

```sh
python -B -s run_prototype.py \
  --detector both --attacker all --seeds 101 \
  --episodes 6 --campaigns 2 \
  --policy-dir .local/faculty-legacy-main \
  --output .local/faculty-legacy-reload
```

The reload workflow performs zero policy-training episodes despite the retained configuration argument; the recorded mode and checkpoint identities establish what ran. A repeat with identical seeds checks reproducibility, not a new independent replication.

## Reproduce the reported results and run tests

The following reconstruction reads the preserved records and regenerates the paper's machine-readable tables without training models. The separate pilot checker verifies the retained main/repeat/reload evidence and recorded learning updates.

```sh
python -B scripts/reproduce_paper.py

python -B verify_mechanism_pilot.py \
  --reference .local/retained/pilot-main \
  --repeat .local/retained/pilot-repeat \
  --reload .local/retained/pilot-reload \
  --output .local/pilot-verification-new.json
```

The last recorded integration selection passed **478 distinct tests**: 420 selected core/legacy/pilot/independent/F5/artifact cases and 58 dashboard cases, with no failures, skips or deselections. That is preserved test evidence, not a claim of a new test run for this README rewrite; the overlapping 47-case RL selection is not added to the total.

<details>
<summary>Exact regression selection and optional paper rebuild</summary>

```sh
python -B -m pytest \
  tests/test_core.py tests/test_milestone1.py tests/test_gate_b.py \
  tests/test_prototype_rl.py tests/test_mechanism_pilot.py tests/test_mechanism_cli.py \
  tests/test_artifact_restore.py test_timing.py test_vpa_strategies.py \
  examples/test_environment.py closeout-tests/test_independent.py \
  f5-evidence/test_schema.py dashboard/test_dashboard.py -q

# Optional analysis/TeX tools; not needed to start the dashboard.
python -m pip install -r requirements-research.txt
python -B scripts/reproduce_paper.py --figures
(cd research/paper && tectonic main.tex --keep-logs)
```

See the [reproducibility guide](docs/REPRODUCIBILITY.md) and [paper build instructions](research/paper/README.md) for artifact identities, environment controls and toolchain details. Existing output and verification paths should be preserved rather than reused for unrelated runs.

</details>

The strengthened retained-pilot verifier passed 1,012,673 checks, including 30,985 recorded TD updates; separate paper reconstruction passed 44,608 record/hash/arithmetic checks. These are verification assertions, not extra test cases, campaigns or independent blocks, and no expensive full study was rerun during integration.

## What the project proves, and what it does not

The evidence supports a working, inspectable synthetic campaign-testing framework and the reported outcomes under its registered conditions. It does not establish a production detector or general real-world UPI protection.

- **Narrow holdout claim:** the pilot excludes the declared gradual-escalation mechanism from registered synthetic detector-development data. Historical detector-training ancestry remains unverified; this is not proof of general detector-unseen fraud.
- **Exploratory comparisons:** nine blocks, two pilot mechanisms, unequal offline training costs and unadjusted contrasts limit conclusions. There is no universal RL-superiority or confirmatory-power claim.
- **Benign-shift failure:** legitimate lookalikes are frequently blocked. The observed rate is a result for this generator and feature representation, not a real customer-population estimate.
- **Financial meaning:** gross simulated debit is neither actual victim loss nor money saved. BLOCK-proposed amounts are rejected proposals, not proven savings.
- **Research status:** no powered untouched-lockbox study or external real-world validation is established. Gate C remains HOLD.

The [limitations and future-work guide](docs/LIMITATIONS_AND_FUTURE_WORK.md) separates completed engineering from proposed experiments. Those follow-up experiments are not silently presented as implemented features.

## Paper, presentation and reviewer resources

- **Academic paper:** [compiled IEEE review draft](research/paper/main.pdf), [LaTeX source](research/paper/main.tex) and [build instructions](research/paper/README.md).
- **Novelty and related work:** [comparison matrix](research/literature_review/comparison_matrix.csv), [qualified contribution](research/literature_review/NOVELTY_ANALYSIS.md) and [source-verification scope](research/literature_review/SOURCE_VERIFICATION.md).
- **Faculty presentation:** [editable slides](research/review_materials/review_deck.pptx), [PDF preview](research/review_materials/review_deck.pdf), [presentation outline](research/review_materials/presentation_outline.md), [Q&A](research/review_materials/questions_and_answers.md) and [live demo script](docs/REVIEW_DEMONSTRATION.md).
- **Evidence and handover:** [verification report](docs/VERIFICATION_REPORT.md), [requirement status](docs/REQUIREMENT_STATUS.csv), [handover](docs/HANDOVER.md) and [full PR file inventory](docs/verification/PULL_REQUEST_FILES.csv).

The paper is an AI-assisted review draft, not an unqualified final submission. Author/institution/venue approval and genuine university-approved AI-content and similarity reports remain [PENDING EXTERNAL VERIFICATION](research/review_materials/EXTERNAL_CHECKS.md); no percentage or threshold compliance is claimed.

The [CI definition](docs/ci/README.md) is a non-executing template because the connected OAuth app lacks workflow permission; no remote CI pass is claimed. Project-license selection remains a copyright-holder decision, as explained in [LICENSE](LICENSE), and [historical reports](docs/history/README.md) retain their original scope rather than overriding current evidence.

Use [CITATION.cff](CITATION.cff) with the exact reviewed commit and artifact identities when citing the project. [Contributions](CONTRIBUTING.md) must preserve records and defensible claims; scientific validity extends only as far as the audit and recorded evidence support, and Gate C remains HOLD.
