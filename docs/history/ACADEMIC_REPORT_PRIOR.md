# UPI Fraud Stress Lab: Scientifically Qualified Academic Report

The project combines a corrected synthetic stress-testing implementation with a new, artifact-bound, matched mechanism-holdout pilot. Provenance and comparison control are stronger, but a major negative finding prevents an unqualified success claim: benign held-out-mechanism episodes suffer substantial false blocking. The defensible contribution is exploratory research infrastructure and an evidence-traceable synthetic case study, not reliable unseen-fraud detection, generic RL superiority or real-world UPI robustness.

## Research question and architecture

Can campaign-level stress testing support reproducible comparisons of fixed, feedback-driven and learned policies, and what happens when a defined synthetic mechanism is excluded from detector development? The contribution is integrated infrastructure, explicit split/action contracts and independent reconstruction of results. Tabular Q-learning, XGBoost and Random Forest are standard algorithms; no new learning algorithm or real payment-system vulnerability is claimed.

The legacy path remains `run_prototype.py` → `src/experiments/prototype.py` → attacker → campaign executor → synthetic ledger/environment → saved detector → records/checker. Its money, terminal/completion reward, checkpoint and frozen-evaluation remediation remains unchanged. The additive path is `src/experiments/mechanism_pilot.py`, reusing that executor/environment and reward observer. `MatchedPolicy` restricts action selection and bootstrap to a common legality mask and adds a label-blind control. `verify_mechanism_pilot.py` independently reconstructs outputs without importing implementation money, reward or TD helpers.

The four detector features are amount, hour, one-hour source transaction count and new-VPA status. Causal feature calculations are checked against actual environment observations. The new study uses one source and one sink with no rotation; gross flow is actual simulated source debit, not unrecovered victim loss.

## Separate experimental versions

The corrected legacy study remains preserved, not overwritten. It uses the original two detector artifacts, three seeds, four attackers, all four campaign families, 1,800 training episodes and 1,152 evaluation campaigns. Its full experiment was not rerun in this mission; a fresh short main/repeat/reload verified continued execution.

The new pilot uses new synthetic data, model fits, action constraints, timing and thresholds. Its results cannot be pooled with the old study or interpreted as a causal improvement over the old implementation. Historical detector-family holdout and stored historical AUC remain unverified; unchanged old results cannot repair that missing provenance.

## New data, models and mechanism holdout

Nine independently generated data/model/policy blocks use deterministic, namespaced seeds. Each block has 1,000 balanced-by-episode benign/HVB fitting episodes, 400 allowed-family validation episodes, 1,000 ordinary benign calibration episodes, 400 ordinary benign test episodes and 400 benign GE-mimic test episodes. Row balance differs from episode balance. Roles are split before feature generation, with unique IDs and no shared evaluation ancestry.

Only registered fitting rows and labels enter `model.fit`. No scaler or SMOTE is used. Fixed XGBoost and Random Forest recipes use 100 depth-4 trees and 150 depth-8 trees respectively, with single-threaded fitting. Per-model fit bindings record matrix/label and raw-row hashes, episode membership, parameters, seed, source identity and pickle hash. The repeat independently fits identical model bytes. This is inspectable execution/input-chain evidence, not an externally authenticated historical training certificate.

HVB starts at nominal 15,000, then uses 8,000/15,000 bands. GE starts at 1,000 and rises through 1,000/3,000/8,000/15,000 with adjacent nondecreasing bands and no more than two repeated proposals below the top band. Final amounts share target clipping. `docs/MECHANISM_PILOT_DESIGN.md` defines the exact grammar and nontrivial prefix predicate; the checker separately implements it.

GE generator/ancestry and signature-positive prefixes are excluded from fit, allowed-family validation and calibration. Signature-positive ordinary benign candidates are quarantined and preserved rather than silently relabeled. This verifies the declared mechanism exclusion in these artifacts; it does not exclude shared scalar feature values, every conceivable escalation mechanism, or researchers' prior knowledge. Slow drain and beneficiary hopping remain implemented/tested in the legacy software but receive no new mechanism-holdout certification.

The GE-mimic benign stratum intentionally follows the excluded mechanism with a benign label. Its sampler is mechanism-matched, not one-to-one paired with every attacker trace. It tests whether unfamiliar legitimate behavior is also rejected.

## Matched policy comparisons

All five arms share the within-mechanism legal mask, four amount bands, two pacing choices, target clipping, fixed beneficiary, funds, target-sized budget, 30-step horizon, 86,400-second duration and outcome definitions. Targets are 20,000–40,000 with cent precision; paces are 300 or 1,200 seconds. First BLOCK terminates; FLAG can transfer; exact target completion defines success.

- **Static:** A fixed rule kernel receives NEUTRAL, selecting the highest legal amount and slow pace.
- **Rule-adaptive:** The same kernel receives actual previous labels; ALLOW selects fast pace and FLAG selects the lowest legal amount and slow pace.
- **Trained RL:** A Q-table sees own progress, remaining horizon and previous label. Training uses alpha 0.25, gamma 0.95 and decaying exploration; evaluation exploration is zero.
- **Blind trained RL:** Same algorithm, training quota and paired contexts/exploration streams, but explicit label state is masked. Detector-dependent rewards remain, so it is not a detector-naive control.
- **Zero-Q:** No learning or trained table; otherwise common legal actions and evaluation tie-breaking setup.

Each trained arm receives 300 HVB episodes per model. Offline training cost is not matched to static/rule/zero-Q; actual query counts can differ despite equal episode quotas. The inherited reward mixes normalized progress, one completion bonus and intervention/effort/unsuccessful-horizon penalties. Selection and nonterminal bootstrap are both legality-masked. The coarse state is partially observed, so no convergence or optimal-training-budget claim is made.

## Calibration, replication and uncertainty

Thresholds use only ordinary-benign calibration episode-maximum scores. Conservative order statistics and `nextafter` handle ties, targeting empirical any-BLOCK ≤0.5% and any-alert ≤2.5%. Invalid/out-of-range thresholds fail rather than silently create an all-ALLOW sentinel. Nominal caps are not population guarantees or equal achieved FPR across models.

Forty paired contexts per family/model/block produce 360 campaigns per detector/family/arm. Main and repeat each execute 18 detector fits, 10,800 policy-training episodes and 7,200 evaluation campaigns; checkpoint reload executes zero fitting/training and repeats evaluation.

The statistical unit is the independent full data/model/policy block, not transactions or repeated outputs. Tables show sample SD across nine block means and fixed-seed exploratory block-bootstrap intervals for six GE contrasts. Intervals are unadjusted, with no confirmatory multiplicity control, equivalence conclusion or powered superiority claim. Nine blocks and forty contexts are a variance/resolution pilot allocation, not a completed power calculation. The earlier five-point practical-effect proposal is not evidence of adequate power.

There is no independently custodied, untouched confirmatory lockbox. This design was frozen before main results but remains exploratory. Fitting exclusion is not synonymous with independent confirmatory validation.

## Raw-record findings

Completion percentages below derive from the 7,200 actual campaign records. The full table, block SDs, gross/attempt means, benign rates and paired intervals are in `CONSOLIDATED_RESULTS.md`.

| Detector / mechanism | Static | Rule | Trained RL | Blind RL | Zero-Q |
|---|---:|---:|---:|---:|---:|
| XGBoost / HVB | 3.611% | 3.333% | 3.333% | 4.444% | 4.167% |
| Random Forest / HVB | 58.333% | 56.667% | 74.444% | 75.278% | 48.056% |
| XGBoost / GE | 1.667% | 75.278% | 43.333% | 42.222% | 50.833% |
| Random Forest / GE | 71.111% | 100.000% | 91.944% | 89.722% | 85.278% |

GE rule-minus-static is +73.611/+28.889 percentage points for XGBoost/Random Forest. This describes the intervention of this rule's feedback input under this simulator, not adaptation in general. Trained-minus-blind is +1.111/+2.222 points with exploratory intervals including zero. Trained-minus-zero-Q is −7.500/+6.667 points; learning advantage is not universal across models.

Ordinary benign testing observed zero BLOCK episodes for either model type, with any-alert 1.556%/2.667%. In contrast, benign GE-mimic BLOCK is **48.278% for XGBoost and 12.806% for Random Forest**, with any-alert 51.722%/14.889%. The models reject unfamiliar legitimate mechanisms too; held-out lineage does not establish useful fraud discrimination. Zero observed ordinary-benign blocking does not establish zero population risk.

New allowed-family row-validation AUC means are 0.944203/0.943563. These are neither GE-test AUC nor validation of old stored AUC. Correlated episode rows and synthetic labels limit interpretation.

Old corrected static/rule known-workload completion remains 100% for both legacy detectors. That retained observation does not support the old headline adaptation paradox; neither the new rule result nor mixed RL results revive that claim.

## Verification and limitations

The final explicit suite passed 410 distinct cases with zero skips/deselections; 47 separately rerun RL cases overlap it. The first new unit attempt had 31 passes and ten failures because the additive adapter read nonexistent `stop_reason` instead of `termination_reason`. The real adapter error was fixed without weakening assertions, and the failed logs remain.

Independent verification performed 1,012,666 checks and replayed all 30,985 training TD updates. It checked membership, hashes, legality, causal features, money, rewards, terminal behavior, complete policy payloads and model identities. Repeat matched 211 selected files; checkpoint reload matched 193, excluding intentionally absent training traces and mode-specific manifest differences. Serialized fitted-model state and complete persisted policy state remained unchanged during evaluation.

Legacy short main/repeat/reload and its strengthened checker also passed. The old expensive full experiment was not rerun. The prior isolated Python 3.11 environment was inspected and `pip check` passed; no new clean installation is claimed. Exact substantive commands/exit records, source/data fingerprints, seeds and failures are retained in `evidence/`.

Timing means are conditional on observing first FLAG/BLOCK; no event is null and completion is a competing outcome. Gross flow and BLOCK-proposed amount are not loss or money saved. Main research limitations include conditioned development data, four limited features, synthetic labels, coarse policy state, only nine independent blocks, uncharged offline learning cost and absent real-world validation.

## Conclusion

The project is ready for academic review as an exploratory synthetic software/reproducibility case study with a transparent negative robustness finding. It is not ready for claiming a reliable new unseen-fraud detector, confirmatory adaptation discovery or production effectiveness; institutional submission requirements have not been checked. Scientific validity is assessed only within these artifacts and assumptions. Gate C remains HOLD.
