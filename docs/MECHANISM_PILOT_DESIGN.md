# Mechanism Pilot: Design Frozen Before Results

This is a new exploratory version, not a confirmatory study or an implementation of every Research Protocol v2 requirement. Old artifacts/results remain a separate version. The new user mission authorizes isolated implementation, fitting and evaluation; Gate C remains HOLD.

## Fixed study

Nine independent blocks use base seed 41000 and namespaced data, fitting, RL and evaluation streams. Each block fits fresh XGBoost (100 trees, depth 4) and Random Forest (150 trees, depth 8), single-threaded, with fixed hyperparameters and no test-directed tuning. Each uses 1,000 balanced-by-episode train episodes, 400 allowed-family validation episodes, 1,000 ordinary benign calibration episodes and two 400-episode benign test strata. Row class balance may differ from episode balance. Preprocessing is the four raw causal features, without a fitted scaler or SMOTE.

Fit/validation/calibration exclude gradual-escalation generation, derived ancestry and nontrivial matching prefixes. HVB starts at 15,000, then 8,000/15,000; GE starts at 1,000 and increases at most one band at a time over 1,000/3,000/8,000/15,000, with no more than two repeated proposals below the top band. Clipped final amounts use their nominal band for the grammar. Signature-positive ordinary benign samples are quarantined, not relabeled. This conditions the development population. A separate benign GE-mimic test stratum has the held-out mechanism but a benign label, exposing ambiguity of fraud intent from these four features.

Five arms share the same within-mechanism legal masks, clipping, 300/1,200-second timing choices, fixed source/sink, 20,000–40,000 target range, target-sized gross budget, initial balance, thresholds, 30 proposals and 86,400-second duration. FLAG transfers and first BLOCK terminates. The static/rule pair uses one kernel with NEUTRAL versus actual last label. RL and blind-RL each train 300 episodes on HVB only, with equal reward/quota and common context/exploration streams; blind-RL masks the explicit label state, not the training reward. Zero-Q never loads trained values. Family state is not a Q-key component; family constrains the common legal mask. This is partially observed, not a convergence claim.

Each detector/arm/block evaluates forty paired contexts per family, for 7,200 attack evaluation campaigns and 10,800 learned-policy training episodes across the study. Selection and TD bootstraps are both legally masked. Policy payloads are frozen and checked after every evaluation episode; model files are hashed and never rewritten during evaluation.

Thresholds use independent benign episode-maximum scores: a conservative deterministic order statistic with nextafter handles ties, targeting empirical any-BLOCK ≤0.5% and any-alert ≤2.5%. These are nominal calibration budgets, not certified population rates. An impossible in-range threshold raises an error; there is no silent all-ALLOW sentinel. No held-out or test label selects model hyperparameters or thresholds.

## Analysis and limitations established in advance

Primary descriptive contrasts on GE are rule-minus-static, RL-minus-blind-RL and RL-minus-zero-Q, separately for each detector. Report block-paired differences, seed SD, and exploratory block-resampling intervals, with a fixed resampling seed. They are not multiplicity-controlled confirmatory discoveries or powered tests. Five absolute completion percentage points is retained as an effect-of-interest sensitivity reference, not a declared detectable effect.

Nine blocks and forty contexts follow the prior protocol's initial variance-estimation/resolution pilot rationale, not a final power calculation. Train/calibration/benign counts are fixed engineering pilot allocations, not population sample-size guarantees; report finite-data uncertainty and model-to-model variation. No final-test custodian or untouched confirmatory lockbox is available in this autonomous exploratory study. Do not retrofit those claims.

Save full episode registries, fit rows and feature/label hashes, actual fitter inputs, model bytes/bindings, quarantine, calibration/test score traces, learned policies, training transitions, evaluation traces, configuration and source hashes. Independently recalculate ledger/feature/count/terminal/reward/summary quantities and replay recorded TD updates. Repeat and checkpoint-only evaluation are reproduction checks, not independent statistical replications.

Failures remain in the record. New correctness changes require a new code identity and fresh output directory, never alteration of earlier output. If the task is ceiling/floor dominated, report it as an uninformative task for superiority, not evidence of equality or a reason to tune the test set. All new findings concern this synthetic constrained mechanism, not the old model provenance, all four-family robustness, real-world UPI or production readiness.
