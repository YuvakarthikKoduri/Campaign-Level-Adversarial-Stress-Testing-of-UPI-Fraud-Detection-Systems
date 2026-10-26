> HISTORICAL SCOPE RECORD: The body below retains earlier claims and workspace paths, not current acceptance. Use the [current README](README.md), [verification report](docs/VERIFICATION_REPORT.md) and [handover](docs/HANDOVER.md) for present commands, counts and limitations. Historical completion/AUC/novelty/production claims are not adopted. Gate C remains HOLD.

# Historical report: pre-remediation implementation only

Current authority is `../FINAL_ACADEMIC_REPORT.md` and
`../FINAL_AUDIT_REPORT.md`. Older closeout/report paths in the historical
body refer to the unchanged package in `../preserved-v1/`.

This historical report is not the closeout verdict. Its original body below
describes an earlier implementation. Read `../FINAL_ACADEMIC_REPORT.md` and
`../CLOSEOUT_REPORT.md` for corrected results, current verification and limits.
The original unchanged report is preserved in `../preserved-reports/`.
Gate C remains HOLD; historical counts and completion claims are not current
scientific-validation evidence.

# UPI Fraud Stress Lab: Academic Prototype Completion

The academic prototype runs end to end with an integrated tabular Q-learning
attacker, real campaign/environment execution, both existing saved detectors,
paired multi-seed comparisons, checkpoint evaluation and reproducible output
tables and plots. The selected expanded suite passed 201 tests. This completes
the defined development demonstration, not scientific validation or Gate C
production readiness; that pilot remains on HOLD.

## Repository and development boundary

- **Inspected repository:** `/home/user/workspace/upi-audit`, branch
  `feature/gate-c-semantic-baseline`, commit
  `c2634021a1979c912755bfef7987e35d03e8b78e`; initially clean.
- **Development copy:** `/home/user/workspace/upi-prototype-dev`, branch
  `prototype/rl-academic`, cloned without hard links from that commit.
  The implementation is an uncommitted working-tree extension. The baseline
  commit is not falsely presented as containing the new code.
- **Original checkout:** final tracked diff was empty and Git status clean.
  The two copied detector files matched the originals byte-for-byte by SHA-256.
  This is a current comparison, not certification of all repository history.
- **Runtime:** existing development venv
  `/home/user/workspace/upi-m1-clean-env/bin/python`, CPython 3.11.17;
  NumPy 2.4.6, pandas 2.2.3, scikit-learn 1.9.1, XGBoost 3.2.0,
  pytest 8.3.3. No new dependency was installed.
- **Excluded:** Gate C production/staging/control paths, real approvals, trust
  pins, reservation, semantic collection/audit/preparation/training/evaluation
  workflows, push, merge and publication. Earlier scratch failures, interpreter
  ancestor-policy failure and absent Gate C import smoke remain unchanged.

The interpreter is used for newly authorized ordinary development. Its successful
prototype runs do not make it compliant with the separate blocked trust policy.

## Audit of actual starting components

| Component | Actual status | Evidence | Missing work at audit | Priority |
|---|---|---|---|---|
| Campaign execution and ledger | Working core with validation, balances, first-BLOCK termination, public feedback | `src/campaigns/executor.py`, `src/environment/simulator.py`; existing core/milestone tests | Optional RL lifecycle/transition hooks | P0 |
| XGBoost / Random Forest | Both saved artifacts present and loadable; legacy experiment executable | `src/detectors/baseline.py`, `models/baseline_*.pkl`; executed tests and both-detector compatibility run | Prototype reuse, not detector retraining | P0 |
| Four families / timing / VPAs | Implemented, not just README features | `generator.py`, `timing.py`, `vpa_strategy.py`, family factory; executed timing/VPA regressions | Define how RL controls map to those simulator capabilities | P1 |
| Static / rule-based adaptive | Existing family-specific factory and feedback-dependent rules | `src/attackers/family_based.py`, `adaptive.py`, `static.py`; baseline tests | Three-way comparison with a genuinely learned policy | P1 |
| Reinforcement learning | No RL agent/Q table/learning loop found in starting attacker code | Direct attacker-module inspection | Implement learning, integration, persistence and tests | P1 |
| Existing experiment entry point | `run_experiment.py` runs S1–S4 on both models and fresh outputs | Executed 48-campaign compatibility run | Separate RL-capable development entry point | P0 |
| Synthetic data | Legacy CSV and generator present; legacy run reads CSV identity | `data/synthetic/upi_transactions_v1.csv`, `src/data/synthetic.py` | No new dataset needed for campaign-based learning | P0 |
| Tests | 134 passed, one genuine stale assertion failed initially | `prototype_evidence/baseline-tests.log/xml` | Assert the actual three-way threshold contract; add RL tests | P3 |
| Semantic Gate C pipeline | Separate authorization-gated implementation, not a runnable approved pilot | Inspected module layout and prior accepted reports | Out of scope; do not use it as an RL shortcut | Excluded |
| Historical results / README percentages | Historical narrative is not current completion evidence | README explicitly labels old claims and limitations | Replace with executed prototype evidence, retain caveats | P4 |
| Legacy training helpers | Multiple older entry scripts; some require optional libraries outside the chosen lock | Static script/dependency inspection | Not needed: existing detector inference works; old retraining paths not validated | Optional |

The initial test failure was `TestEnvironment.test_process_transaction`: a
legitimate FLAG was rejected by an assertion allowing only ALLOW/BLOCK. The
correction accepts all three supported outcomes and additionally asserts exact
agreement with the configured threshold decision. It does not conceal or
reclassify the original failure.

## Implementation and changed files

- **New RL module:** `src/attackers/q_learning.py`.
- **New experiment API / CLI:** `src/experiments/prototype.py`, `run_prototype.py`.
- **New plots:** `src/experiments/prototype_plots.py`, dependency-free SVG output.
- **New tests:** `tests/test_prototype_rl.py`, 47 collected cases in the final suite.
- **Targeted existing-code change:** `src/campaigns/executor.py`, optional episode
  hooks, RL transition evidence and proposal counting. Existing actors do not
  need to implement those hooks.
- **Contract correction:** `tests/test_core.py`, the stale FLAG assertion.
- **Documentation:** README prototype section, `docs/PROTOTYPE_GUIDE.md`, this report.
- **Delivery helper:** `build_prototype_delivery.py`.
- **Generated evidence:** separate files/directories beneath `prototype_evidence/`.
  Original baseline/failed evidence and earlier successful runs were retained.

No existing detector artifact, dependency lock, Gate C config or authorization
loader was changed. Model SHA-256 observations are:

```
baseline_xgboost.pkl
e1cea0538349f6fba1e9a4efcf85f9d871c7a2c3409c7a0d4d3b0649e2f2e162

baseline_random_forest.pkl
e1d072db72072ab0844961f073109093ed63484411fb5539458211213658cd43
```

## RL algorithm and learning evidence

Tabular Q-learning was chosen because the prototype has a small interpretable
space: at most 64 states and 16 actions. It fits the existing choose/observe
interface without a new neural-network framework.

- **State:** progress toward own target, remaining step fraction and last public
  decision, each discretized in 0..3. No detector score, test label, future event,
  private feature vector or private ledger is provided to the agent.
- **Actions:** four amounts (1,000/3,000/8,000/15,000), two pacing choices (family
  minimum/maximum), and recipient reuse/rotation. Existing source-VPA selection,
  timestamps, feasibility checks and controlled recipient pool are retained.
  The final amount is clipped to the remaining target.
- **Reward:** `3*min(transferred/target,1) + 2*success - BLOCK - 0.2*FLAG
  - 0.02 - 0.5*unsuccessful_step_horizon`; no extra horizon penalty on BLOCK.
  Rejection before feedback has terminal reward -1.02. This balances progress,
  completion, detection/intervention and per-attempt effort rather than stealth
  alone; it is not calibrated economic utility.
- **Learning:** alpha 0.25, gamma 0.95, epsilon linearly 1.0 to 0.05.
  Terminal transitions have no bootstrapped future value. Training episodes
  update Q; evaluation freezes Q updates and conditions actions on observed state.
- **Persistence:** versioned JSON Q table and hyperparameters, with detector,
  seed, threshold and horizon metadata checked on CLI reload. This is
  reproducible evaluation, not exact mid-training RNG-state resumption.
- **Controlled learning test:** a real simulator fixture blocks amounts above
  3,000. After training, the greedy policy selects safe actions and completes
  the target; assertions inspect actual actions and Q-value ordering.

Across the primary training runs, the observed update counts were XGBoost
1,105/1,074/1,189 and Random Forest 1,177/1,136/1,115. Every evaluation run
recorded zero further learning updates. Average training reward over the first
50 versus last 50 episodes, averaged across three seeds, increased from
2.975 to 4.610 for XGBoost and 3.305 to 4.833 for Random Forest.
These are training diagnostics, not proof of universal superiority.

## Experiment protocol and comparison

Primary output: `prototype_evidence/comparison-final/`.
Seeds: 101, 202, 303; 300 training episodes per detector/seed; 30-step horizon;
24 evaluation campaigns per kind/attacker/detector/seed; thresholds FLAG 0.40,
BLOCK 0.70. The two detectors, two workload kinds and four attacker variants
produce 1,152 evaluation campaigns plus 1,800 primary training episodes.

Each table cell below contains 72 evaluation campaigns. Unknown workloads
contain eight campaigns per held-out family per seed. Means and sample SDs
are across three seed-level means, not across dependent transactions.

| Detector | Workload | Attacker | Success %, mean ± seed SD | Mean attempts | Mean gross transferred exposure |
|---|---|---|---:|---:|---:|
| XGBoost | Known | Static | 100.0 ± 0.0 | 1.736 | 43,751.30 |
| XGBoost | Known | Rule-adaptive | 100.0 ± 0.0 | 1.736 | 40,820.72 |
| XGBoost | Known | RL | 100.0 ± 0.0 | 2.833 | 29,752.09 |
| XGBoost | Unknown | Static | 90.3 ± 6.4 | 6.528 | 15,699.80 |
| XGBoost | Unknown | Rule-adaptive | 98.6 ± 2.4 | 6.597 | 16,406.42 |
| XGBoost | Unknown | RL | 100.0 ± 0.0 | 1.472 | 14,680.31 |
| Random Forest | Known | Static | 100.0 ± 0.0 | 1.736 | 43,751.30 |
| Random Forest | Known | Rule-adaptive | 100.0 ± 0.0 | 1.736 | 44,302.18 |
| Random Forest | Known | RL | 98.6 ± 2.4 | 3.167 | 29,735.24 |
| Random Forest | Unknown | Static | 94.4 ± 2.4 | 6.542 | 15,972.90 |
| Random Forest | Unknown | Rule-adaptive | 97.2 ± 4.8 | 6.667 | 16,191.61 |
| Random Forest | Unknown | RL | 100.0 ± 0.0 | 1.653 | 14,680.31 |

The zero-Q/untrained action-space control reached 58.3% ± 7.2% on known
workloads for both detectors and 100% on unknown workloads. Thus the learned
policy substantially improved known-workload success over its own untrained
action vocabulary, but unknown-workload success alone does not demonstrate
a learning advantage. RL was also below static/rule-adaptive on Random Forest
known-workload success, not universally superior.

RL does not always reduce detection: for example, XGBoost unknown RL campaigns
had a mean 1.014 FLAGs and zero BLOCKs, compared with static 0.764 FLAGs and
0.097 BLOCKs. First FLAG at time zero is a genuine observed detection, not
missing data; absent detections/interventions remain null with observed counts.

Exposure is the sum of amount transferred, including FLAG transfers, not
unrecovered monetary loss. RL target clipping versus legacy overshoot is an
important exposure confound; lower RL exposure is not evidence of a better
detector. The untrained control shares the clipping/action vocabulary.

S1/S2 retain known-family static versus feedback-dependent structure; S3/S4
retain other-family static versus feedback-dependent structure, with an explicit
attacker column distinguishing rule-adaptive and RL. RL trains only on
HIGH_VALUE_BURST and transfers to the other three families. Their historic
“unseen to detector” status is nominal because old detector-training provenance
does not establish strict leave-family-out validation. A common RL amount
vocabulary also means family labels do not guarantee legacy amount trajectories.

## Executed tests and repeatability

| Invocation / evidence | Result |
|---|---|
| Initial baseline, `baseline-tests.log/xml` | 134 passed, 1 failed, 0 skipped; failure preserved |
| First RL-specific suite, `rl-tests-first.log/xml` | 46 passed, 0 failed |
| Initial combined suite, `regression-final.log/xml` | 181 passed, 0 failed |
| Expanded final suite, `regression-expanded.log/xml` | 201 passed, 0 failed, 0 skipped; one retained XGBoost portability warning |
| Legacy S1–S4 compatibility run, `legacy/compatibility-01/` | Both detectors, 6 campaigns/scenario, 48 campaigns; completed |
| Primary full RL comparison, `comparison-final/` | 1,800 training episodes, 1,152 evaluation campaigns; completed |
| Full repeat, `comparison-repeat/` | Results, curves, plots, manifest and all six Q checkpoints byte-identical |
| Checkpoint-only run, `evaluation-loaded/` | 1,152 evaluation campaigns; zero training episodes; results byte-identical |
| Short CLI demonstration, `demo-short/` | 120 training episodes and 96 evaluation campaigns; completed |
| Extracted delivery archive | All 206 initial bundle-file hashes matched; both-detector CLI demo completed 40 training / 48 evaluation episodes; 47 RL tests passed, 0 failed, 0 skipped |

The final 201 cases include core/milestone/Gate B regressions, all new RL cases,
root timing/VPA tests and example-environment tests. The 47 RL cases cover
state/action validity, all 16 action combinations and pacing, reward arithmetic,
Q updates, exploration/exploitation, terminal/invalid transitions, fixed seeds,
save/load and mismatch rejection, both real detectors, frozen evaluation,
end-to-end serialization/repeatability and reserved-output rejection.

Gate C tests were deliberately not run: `test_gate_c_contract_edges.py`,
`test_gate_c_generation.py`, `test_gate_c_policy.py`, `test_gate_c_integrity.py`,
`test_gate_c_models.py`, `test_gate_c_storage.py`. “Zero skipped” describes the
selected suite, not an assertion that those excluded tests executed.
The legacy `test_families.py` main-style demonstration was inspected but not
counted as a pytest case or used as current family-coverage evidence.

No original failure evidence was overwritten. An initial orchestration command
also exited 1 before launching pytest because its log redirection used the
workspace cwd rather than the new copy; the subsequent baseline invocation
specified the correct cwd. This was an infrastructure mistake, not a hidden
test failure or a pilot action.

## Exact execution and reproduction commands

Repository inspection included `git branch --show-current`, `git rev-parse HEAD`,
`git status --short`, `rg --files`, source reads, runtime/version checks and model
metadata/hash inspection. Development initialization was:

```sh
git clone --no-hardlinks /home/user/workspace/upi-audit /home/user/workspace/upi-prototype-dev
git -C /home/user/workspace/upi-prototype-dev switch -c prototype/rl-academic
cp --no-clobber /home/user/workspace/upi-audit/models/baseline_xgboost.pkl \
  /home/user/workspace/upi-audit/models/baseline_random_forest.pkl \
  /home/user/workspace/upi-prototype-dev/models/
cp --no-clobber /home/user/workspace/upi-audit/data/synthetic/upi_transactions_v1.csv \
  /home/user/workspace/upi-prototype-dev/data/synthetic/
mkdir /home/user/workspace/upi-prototype-dev/prototype_evidence
```

The execution commands below ran from the development copy with
`OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
PYTHONDONTWRITEBYTECODE=1`; deterministic comparison/test commands additionally
used `PYTHONHASHSEED=17 TZ=UTC`. `P` below is a report abbreviation for
`/home/user/workspace/upi-m1-clean-env/bin/python -B -s`, not another program.
Stdout/stderr were retained in the named evidence logs.

```sh
P -m pytest tests/test_core.py tests/test_milestone1.py tests/test_gate_b.py \
  -q --junitxml=prototype_evidence/baseline-tests.xml
P -m pytest tests/test_prototype_rl.py -q \
  --junitxml=prototype_evidence/rl-tests-first.xml
P run_experiment.py --scenario all --detector both --campaigns 6 --seed 999 \
  --max-steps 30 --output-dir prototype_evidence/legacy --run-id compatibility-01
P -m pytest tests/test_core.py tests/test_milestone1.py tests/test_gate_b.py \
  tests/test_prototype_rl.py -q --junitxml=prototype_evidence/regression-final.xml
P -m pytest tests/test_core.py tests/test_milestone1.py tests/test_gate_b.py \
  tests/test_prototype_rl.py test_timing.py test_vpa_strategies.py \
  examples/test_environment.py -q --junitxml=prototype_evidence/regression-expanded.xml
P run_prototype.py --detector both --attacker all --seeds 101 202 303 \
  --episodes 300 --campaigns 24 --max-steps 30 \
  --output prototype_evidence/comparison-default
P run_prototype.py --detector both --attacker all --seeds 101 202 303 \
  --episodes 300 --campaigns 24 --max-steps 30 \
  --output prototype_evidence/comparison-final
P run_prototype.py --detector both --attacker all --seeds 101 202 303 \
  --episodes 300 --campaigns 24 --max-steps 30 \
  --output prototype_evidence/comparison-repeat
P run_prototype.py --detector both --attacker all --seeds 101 202 303 \
  --episodes 300 --campaigns 24 --max-steps 30 \
  --policy-dir prototype_evidence/comparison-final \
  --output prototype_evidence/evaluation-loaded
P run_prototype.py --seeds 101 --episodes 60 --campaigns 6 --max-steps 30 \
  --detector both --attacker all --output prototype_evidence/demo-short
```

Baseline pytest exited 1; the other listed test/experiment invocations exited 0.
`comparison-default` is retained pre-checkpoint-metadata evidence, not relabeled
as the final source version. `comparison-final` and its repeat used final runtime
code. Repeated commands represent intentional reproducibility checks, not added
independent evaluation samples.

`cmp` returned 0 for final/repeat campaign, summary, per-seed, transaction,
learning, plot and manifest files and six Q checkpoints. Final/loaded campaign,
summary, per-seed, transaction and comparison-plot files also matched. Final
source `git diff --exit-code HEAD` returned 0, and its porcelain status was empty.
SVG files parsed as XML; charts are derived from saved values, not illustrative
numbers. The delivery hash manifest provides individual file identities.

The delivery was also tested after extraction into a different project path,
using the unchanged existing development venv (not a newly installed environment).
Its commands, all exit 0, were:

```sh
P build_prototype_delivery.py /home/user/workspace/upi-fraud-stress-lab-prototype-verification.zip
P -m zipfile -e /home/user/workspace/upi-fraud-stress-lab-prototype-verification.zip \
  prototype_evidence/package-check
cd prototype_evidence/package-check/upi-fraud-stress-lab-prototype
sha256sum -c DELIVERY_SHA256SUMS.txt
P run_prototype.py --detector both --attacker all --seeds 909 --episodes 20 \
  --campaigns 3 --max-steps 30 --output packaged-demo
P -m pytest tests/test_prototype_rl.py -q --junitxml=../../package-rl-tests.xml
```

Evidence is retained in `prototype_evidence/package-hashes.log`,
`package-demo.log`, `package-rl-tests.log` and `package-rl-tests.xml`.
The final archive additionally contains those logs, this updated report,
the presentation material and the reusable output verifier; runtime source
and original detector artifacts are unchanged from the tested archive.
The extracted duplicate is excluded from delivery to avoid recursive bundling.

For a fresh reproduction, unpack the delivered archive, enter its root and
follow `docs/PROTOTYPE_GUIDE.md`. That guide gives environment installation,
short/full demos, single-attacker selection, checkpoint evaluation and tests.
Use a new output path: collisions raise rather than overwriting old evidence.

## Saved outputs and deliverables

- **Working source:** the development copy and the source/evidence ZIP.
- **Primary tables:** `prototype_evidence/comparison-final/summary.csv`,
  `summary.json`, `per_seed.csv`.
- **Transaction and campaign evidence:** `transactions.csv`, `campaigns.json`,
  including per-step decisions and RL state/action/reward records.
- **Learning and policies:** `learning.csv`, six `q_DETECTOR_SEED.json` files.
- **Plots:** `comparison.svg` and `learning.svg`, attached separately and bundled.
- **Reproduction guide:** `docs/PROTOTYPE_GUIDE.md`.
- **Presentation material:** `docs/architecture.svg` and
  `docs/PRESENTATION_BRIEF.md`, including a short live demo and a one-command
  main experiment.
- **Test evidence:** initial and final logs/JUnit XML, with failures retained.

## Completion checklist and limitations

| Requirement | Verified status |
|---|---|
| P0 runnable baseline and end-to-end experiment | Complete for the development prototype |
| P1 genuine integrated RL, learning and persistence | Complete; actual Q updates, action influence, save/load and frozen evaluation tested |
| P2 static / rule-adaptive / RL multi-seed comparison | Complete; extra same-action-space untrained control included |
| P3 essential RL, integration, regression and end-to-end tests | Complete for the selected 201-case suite; Gate C deliberately excluded |
| P4 setup, architecture, metrics, limitations and demo instructions | Complete in this report and the guide |
| P5 advanced agents, dashboard, additional models | Not pursued; unnecessary for the academic definition of done |
| Production security / Gate C authorization | Outstanding and outside this task |
| Empirical UPI realism / research validity / strict detector-held-out generalization | Not established |

The data and account network are synthetic; historic detector pickle portability
and incomplete training provenance remain limitations. Three seeds are not a
significance study. Reward weights are subjective, state is coarse/partially
observable, gross flow is not financial loss, and actor action spaces are not
matched except in the explicit untrained control. Zero observed evaluation
updates and repeatability do not prove a secure sandbox.

No material defect was left failing in the executed essential development tests.
The academic definition of done is satisfied by demonstrated functionality, not
a README percentage. This report makes no claim that every legacy helper,
restricted workflow or research claim is complete. Work stops here for review;
Gate C and all separately restricted downstream activity remain unauthorized.
