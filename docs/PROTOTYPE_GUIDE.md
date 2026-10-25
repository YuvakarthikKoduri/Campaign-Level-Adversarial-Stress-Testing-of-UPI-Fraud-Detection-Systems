# Academic prototype: reproducible RL demonstration

This is an ordinary-development extension of the legacy campaign simulator, not
the held Gate C semantic pilot. It reuses the existing saved XGBoost and Random
Forest detectors and the existing campaign/environment ledger. Gate C approval,
collection, audit, preparation and model workflows are neither invoked nor
authorized by these commands.

## Setup and demonstration

Use Python 3.11 on Linux. The delivered archive includes the two original
detector artifacts and the synthetic dataset needed by the legacy runner.
Only load model pickle files supplied with this project, never untrusted ones.
The detector's existing XGBoost portability warning is retained.

```sh
python3.11 -m venv .venv-prototype
. .venv-prototype/bin/activate
python -m pip install -r requirements-milestone1.lock
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONHASHSEED=17 PYTHONDONTWRITEBYTECODE=1 TZ=UTC

# Short demo: both detectors, four attacker variants, all four families.
python -B -s run_prototype.py --seeds 101 --episodes 60 --campaigns 6 \
  --max-steps 30 --detector both --attacker all --output demo-short

# Full reported comparison, a fresh output directory is mandatory.
python -B -s run_prototype.py --seeds 101 202 303 --episodes 300 \
  --campaigns 24 --max-steps 30 --detector both --attacker all \
  --output demo-full

# Re-evaluate those exact saved Q policies, without training.
python -B -s run_prototype.py --seeds 101 202 303 --episodes 300 \
  --campaigns 24 --max-steps 30 --detector both --attacker all \
  --policy-dir demo-full --output demo-loaded

# Recompute the delivered full-repeat/reload evidence (fresh JSON output).
python -B -s verify_prototype_outputs.py \
  --reference prototype_evidence/comparison-final \
  --repeat prototype_evidence/comparison-repeat \
  --reload prototype_evidence/evaluation-loaded --output reviewer-check.json

# Select a single detector and attacker.
python -B -s run_prototype.py --detector xgboost --attacker rl \
  --seeds 101 --episodes 60 --campaigns 3 --output demo-rl

# Regression, RL and end-to-end checks; deliberately no Gate C test workflows.
python -B -s -m pytest tests/test_core.py tests/test_milestone1.py \
  tests/test_gate_b.py tests/test_prototype_rl.py \
  test_timing.py test_vpa_strategies.py examples/test_environment.py -q
```

These are development commands, not a certification that this runtime satisfies
the separate Gate C interpreter-ownership policy. No permission changes,
privilege elevation or production security fallback are required or implied.
The pinned dependency lock was reused; no new plotting or RL package is needed.

## Architecture and scenario definitions

- **Simulator integration:** `CampaignExecutor` invokes optional episode-start
  and episode-end hooks. `QLearningAttacker.choose_action` produces the same
  transaction dictionaries as existing attackers, and `observe` receives only
  the existing label-only public feedback. All actors use the real environment
  inference, feasibility checks, balances and first-BLOCK termination.
- **Static:** the existing family-based `make_attacker(adaptive=False)`. Amount
  trajectories, random timing and recipients may vary, but not in response to
  detector feedback. Static does not mean literally identical transactions.
- **Rule-adaptive:** the existing `make_attacker(adaptive=True)` policy. Its
  amount/recipient rules respond to prior outcomes; it is not called RL.
- **RL:** tabular Q-learning, trained before evaluation. Frozen evaluation still
  conditions action selection on progress and observed decisions; it does not
  update Q values on evaluation campaigns.
- **Untrained RL control:** the identical action space and transaction builder
  with zero Q values and seeded random tie-breaking. This separates evidence of
  learning from advantages caused simply by changing the action vocabulary.
- **S1/S2:** HIGH_VALUE_BURST workload, static versus feedback-dependent attackers.
  Both rule-adaptive and trained RL have an explicit attacker column within S2.
- **S3/S4:** SLOW_DRAIN, GRADUAL_ESCALATION and BENEFICIARY_HOPPING workload,
  static versus feedback-dependent attackers. Families are balanced by quota.
  RL trains only on HIGH_VALUE_BURST; these three families are held out from RL
  training. Their historic designation as unseen to the detector is nominal:
  the old detector artifacts do not establish strict family-held-out provenance.

Family identity controls the simulator's pacing range and workload construction.
The RL agent has a common action vocabulary across families, so its amount
trajectory need not reproduce the named family's legacy shape. Family coverage
here is workload coverage, not proof of four authentic fraud mechanisms.
Untrained RL is an ablation column, not a claimed adaptive learning algorithm.

Training seeds are SHA-256-derived from each evaluation seed with a separate
`prototype-training` namespace; no evaluation episode is used for Q updates.
All compared actors receive the same workload specs, target, account pool,
source-selection seed and family timing bounds. Their actions can of course
make later trajectories differ. This is not an entity-held-out real-data study.

## RL definition

The tabular method fits a small discrete state/action space and is inspectable
without deep-learning dependencies. It is a finite-history approximation, not a
claim that the detector environment is fully observable or Markov.

- **State:** three integer bins in 0..3: transferred progress/target, remaining
  fraction of the step horizon, and last observed decision (START/ALLOW/FLAG/BLOCK).
  At most 64 state keys exist. There is no access to labels, detector scores,
  internal features, future transactions or the environment's private ledger.
- **Actions:** 16 combinations of amount (1,000/3,000/8,000/15,000), pacing
  (family minimum or maximum interval), and recipient reuse/rotation within the
  controlled account pool. The existing VPA selector chooses the source.
  Amount is clipped to the remaining declared target; the executor still applies
  its transaction, budget, time and account feasibility rules.
- **Reward:** `3*min(transferred/target,1) + 2*success - 1*BLOCK - 0.2*FLAG
  - 0.02 - 0.5*unsuccessful_step_horizon`, with the horizon penalty excluded
  on a BLOCK. Rejection before feedback gets a terminal -1.02 penalty.
  Progress is gross transferred amount; FLAG transfers still count. The bonus
  rewards completion, while attempt/flag/block costs discourage inefficient,
  detected or blocked execution. These weights are an explicit academic design
  choice, not calibrated economic utility. There is no stealth-only objective.
- **Update:** `Q(s,a) += alpha*(reward + gamma*max Q(next_state) - Q(s,a))`;
  terminal transitions have zero future value. Defaults are alpha=0.25,
  gamma=0.95. Epsilon decreases linearly from 1.0 to 0.05 during training.
- **Termination:** target reached, first detector BLOCK, step/time horizon,
  budget/feasibility rejection or attacker stop. Evaluation Q updates are
  checked to remain zero. Episode-local history resets; trained Q is retained.
- **Persistence:** versioned JSON action schema, Q table, hyperparameters and
  update count. CLI checkpoints include detector digest, seed, horizon and
  threshold metadata, which must match on reload. RNG state is not persisted
  for exact mid-training resumption; each evaluation campaign reseeds its
  policy stream, making checkpoint evaluation reproducible.

## Metrics, outputs and interpretation

- **Success:** fraction reaching the target before termination.
- **Proposals:** non-null transaction actions submitted to the executor.
  Rejections before execution are reported separately.
- **Attempted:** transactions actually evaluated/recorded by the environment;
  equals ALLOW + FLAG + BLOCK in valid completed experiment records.
- **Exposure:** sum of `amount_transferred`, including FLAG transfers. This is
  gross ledger flow, not net victim loss: transfers can circulate among controlled
  accounts and there is no recovery, real victim or real UPI network.
- **Detection:** first FLAG or BLOCK. **Intervention:** first BLOCK.
  Missing observations remain null/censored, never substituted with zero;
  observed timing means are accompanied by observed counts.
- **Variability:** arithmetic means of seed-level campaign means and sample
  standard deviation across seeds. Three seeds are exploratory, not a powered
  significance study. Within-campaign transactions are not independent samples.

`campaigns.json` includes immutable specs, all transaction decisions/features,
outcomes and RL transitions. `transactions.csv` is a flat decision trace.
`summary.csv`, `summary.json` and `per_seed.csv` provide comparison tables.
`learning.csv` records per-episode rewards, epsilon, success and Q update count.
`q_DETECTOR_SEED.json` stores the policies. `comparison.svg` and `learning.svg`
are dependency-free plots. `manifest.json` records model/source/lock identities,
versions and train/evaluation update counts. Outputs never overwrite an
existing directory. A policy-only run has an empty learning CSV and no training
curve, because it did not perform training.

RL and the rule policies do not have identical action distributions. In
particular, RL clips the final amount to the target, whereas the legacy actors
can overshoot; this affects exposure and is not detector improvement.
Reward improvements alone do not establish superior campaign success, stealth,
generalization or better fraud detection. Use the untrained-action-space
control and the separate success, flags, blocks and exposure metrics.

Historical adaptation-paradox figures remain unvalidated. The earlier all-ALLOW
Gate C pilot proposal could not validate feedback adaptation, and the scratch
controller/import-smoke findings have not been changed by this prototype.
