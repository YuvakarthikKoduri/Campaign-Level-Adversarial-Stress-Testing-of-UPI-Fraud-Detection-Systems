# Gate C semantic baseline: implementation-only review

This local implementation builds on accepted Gate B commit `6b543895769d4e355d775b05c3a3f01f3c1ca8ef`. It implements future execution interfaces, not an executed or accepted semantic dataset/model baseline.

## Authorization boundary

- **Allowed now:** Source implementation, local commits, deterministic literal-fixture unit tests, and the existing regression tests. No approval file for a workflow is provided.
- **Blocked now:** Production preflight, pilot/other generation, bulk preparation, estimator fitting, threshold search/calibration, final-test scoring, research evaluation, push, merge, and publication.
- **Future execution:** Each public workflow checks an `ExecutionPermit` before accessing its workflow inputs or outputs. The CLI additionally requires `--approval-file`, exact configuration digest, explicit execution ID, and an approved phase.
- **Not a security sandbox:** The approval file is an auditable procedural guard, not a cryptographic signature, filesystem ACL, or protection against someone deliberately bypassing Python interfaces. Joblib reload is only for trusted, locally produced artifacts. A human must separately approve the named execution and its reviewed source.

No passing fixture test establishes that generation, fitting, reload of a new fitted model, calibration, or production repeatability succeeds. Those paths remain unexecuted until separate authorization.

## Semantic and causal contract

The shared schema, event/history classes, extractor and encoder are unchanged. Contract ID is `upi_source_attempt_features/2.0.0`, with feature order `amount`, `hour_of_day`, `velocity_1h`, `is_new_vpa`, encoded as float64.

- **Novelty:** First-observed exact source VPA, before the current admitted attempt; beneficiary-only appearances and registration do not consume novelty.
- **Velocity:** Prior valid scored ALLOW/FLAG/BLOCK attempts for that exact source in `(t - one hour, t]`, excluding the current attempt. Same-timestamp observations are ordered by committed sequence; future events cannot enter history.
- **History:** One cold-start namespace per component, independent across episodes. No warm start, cross-component merchant, replenishment, recovery, refunds, or real bank data.
- **Admission:** Candidate sequence counts proposals; event sequence counts successfully processed observations. Invalid/ineligible proposals are recorded as rejected without advancing history. Scoring, ledger, history and sequence failures invalidate the run. An external journal error restores the prior published in-memory state and invalidates the run; incomplete on-disk evidence is retained, not reused as a complete artifact.
- **Observer:** `CollectionObserver` produces a fixed nonlearned zero to exercise the successful scoring/admission stage. It is not a learned fraud probability. Journal `fraud_probability` is null; `collector_score` is zero for admitted attempts. The inherited diagnostic `risk_score` is the same compatibility score, not a probability estimate.
- **Labels:** Hidden intent follows seeded component schedule metadata, independently of detector outputs. Labels/families are attached after processing and live outside `FeatureEvent` and the model matrix. Rejected proposals retain audit labels but are excluded from training rows.

`semantic_entities.py` creates an account/alias graph and declared creation times/balances. `semantic_generator.py` proposes source, beneficiary, amount and time through bounded causal processes; it never samples novelty or velocity. Amounts are clipped and rounded to integer paise, delays to microseconds, with explicit same-time ordering. Fraud labels denote synthetic sender intent, not verified real-world fraud.

SHA-256 role-key seeds use canonical JSON `["upi-gc-seed-v1", root, role, ...keys]`, first 128 bits, with NumPy PCG64. Roles cover split allocation, entities, balances, intent schedules, start times, per-candidate behavior and per-candidate timing; fitting uses a separately derived 32-bit model seed. Candidate keys use proposal sequence, so rejection does not shift later streams. Execution IDs do not enter generation streams.

## Versioned engineering assumptions

`configs/semantic_v2/gate_c_v1.json` is the fully resolved configuration. Its values are synthetic engineering choices, not measured UPI behavior or guarantees of support, model quality or financial realism.

- **Profiles:** Baseline has 1,000 components, a 96-candidate cap, 600/200/200 component allocation and four-hour horizon. Pilot has 24 components, a 24-candidate cap and 14/5/5 allocation. Pilot artifacts are barred from model and policy inputs.
- **Entities:** 8–16 accounts/component, 1–2 aliases/account, no cross-component beneficiary. Balances use the declared clipped lognormal recipe; account/VPA creation times predate the split window.
- **Processes:** Explicit benign/mixed weights, source/payee reuse, overlapping amount/timing recipes, four intent families and a proposal-position intent schedule. The terminal over-horizon candidate is rejected and recorded.
- **Splits:** Disjoint components, account IDs, aliases, beneficiaries and namespaces; separate January 2026 UTC windows with a one-day gap. Membership is not stratified or changed after seeing outcomes.
- **Models:** Only the existing model types, CPU XGBoost and Random Forest, fixed parameters and one worker. No search, resampling, early stopping, validation fitting or test fitting.
- **Calibration:** Validation only, 0.001 threshold grid, benign BLOCK budget 1%, review-or-BLOCK budget 5%; minimum 2,000 benign rows, 200 fraud rows, 50 benign components and 20 fraud components. These support requirements intentionally make a small pilot insufficient.

Any changes to these assumptions require a new reviewed configuration, distinct digest and fresh execution ID; they must not be made to improve observed performance.

## Lineage, splits, models and policies

Preparation replays admitted/rejected journal records against initial entity balances, then recomputes feature vectors with the shared offline extractor and compares them to online vectors. Independent graph checks reject entity overlap, alias bridges, cross-component beneficiaries, duplicate events, noncontiguous sequence and temporal violations.

The dataset stores separate feature/label tables, exact row membership, split event IDs, exclusions, entity metadata, canonical events, full config and a sealed-test declaration. Validation rechecks journal-to-dataset lineage, latent labels, feature values, row links, exact split coverage, manifest/checksum integrity and the test seal. Structural test-partition checks are permitted; model APIs allow training rows for fitting/readiness/reload and validation rows only for calibration, never test rows.

Training records package/runtime versions, source commit, parameters, effective library parameters, dataset manifest hash, schema/extractor digests, model seed, native model hash and training inference bytes. XGBoost uses native JSON; RF uses trusted joblib. Train-time reload and independent later reload compare inference bytes exactly in the pinned environment. None of these fitted-model operations has run under implementation-only authorization.

Probability-model identity does not include thresholds. Calibration freezes the probability model and ranks feasible FLAG/BLOCK pairs by BLOCK true positives, then review-or-BLOCK true positives, then fewer benign BLOCKs, then fewer benign reviews, then higher BLOCK and FLAG thresholds. Budgets use exact rational comparisons; insufficient support or no feasible pair is a hard failure, not a fallback policy. Inclusive comparisons are `score >= threshold`.

Readiness code uses small training-prefix clones for conditional one-step online/offline checks. It does not continue an all-ALLOW collection ledger after a learned BLOCK or mistake that counterfactual for a research trajectory. Final-test scoring, S1–S4 studies and generalization remain Gate D work.

## Actual artifact layout and deviations from the proposal

Completed payloads are immutable with exclusive reservations, private staging, manifest hashes, checksum index and final atomic directory rename. Collisions fail; there is no force/resume/cleanup option. Failed stages retain their payload and reservation, but a failed publication revokes the staged COMPLETE marker. The process-level publication contract is not a multi-host transaction or a power-loss durability guarantee.

```text
data/semantic_v2/<execution_id>/
  collection/{entities.json,journal.jsonl,component_counts.json,seed_contract.json,config.json}
  dataset/
    {entities.json,events.json,membership.json,exclusions.json,test_seal.json,config.json}
    train/{features.json,labels.json,event_ids.json}
    validation/{features.json,labels.json,event_ids.json}
    test/{features.json,labels.json,event_ids.json}
models/semantic_v2/<execution_id>/
  xgboost/{model.json,configuration.json,effective_parameters.json,
           booster_configuration.json,training_ids.json,train_probabilities.f64}
  random_forest/{model.joblib,configuration.json,effective_parameters.json,
                 training_ids.json,train_probabilities.f64}
  policies/<detector>/policy.json
results/semantic_v2/gate_c/<execution_id>/
  preflight/{preservation.json,config.json}
  dataset_validation/checks.json
  model_validation_<detector>/checks.json
  readiness_<detector>/checks.json
  preservation/verification.json
  repeat_<other_execution_id>/checks.json
  closure/review.json
  invocations/<command_and_target>/{request.json,outcome.json}
```

Every completed directory also contains `artifact_manifest.json`, `checksums.sha256` and `COMPLETE`. Schema/extractor digests and lineage are in each artifact manifest rather than duplicated standalone schema files. No actual execution tree above is created by this implementation review.

Implementation deliberately uses canonical JSON tables instead of CSV, detector-named local directories with content IDs in manifests instead of content-ID directory names, and closure evidence instead of a separately published baseline bundle. Immutable per-command request/outcome receipts substitute for a mutable append-only execution journal; external shell capture is still needed for complete native-library console logs. These are storage/interface deviations for review, not hidden equivalence claims. Batch preparation/provenance code lives in the new pipeline package; accepted Gate B fixture codec/provenance and fixture-detector files remain unchanged.

The same semantic payload can have different run-envelope manifest hashes and model IDs across independent execution IDs. Repeat checks compare complete collection/dataset payload hashes, model configuration/training IDs/prediction bytes, native model bytes and selected policy values; they do not ignore model-byte differences. Execution envelope hashes are not required to be identical.

## Supported interfaces and expected results

Only the fixture/regression commands below were authorized for this implementation review. See the external review report and raw logs for actual totals; do not infer execution success from this command list.

```bash
TZ=UTC python -m pytest tests/test_gate_c_*.py -v
TZ=UTC python -m pytest tests test_timing.py test_vpa_strategies.py \
  examples/test_environment.py test_families.py -v
TZ=America/Los_Angeles python -m pytest tests/test_gate_c_*.py -v
```

The future CLI is `python -m src.semantic_pipeline.cli <command>` with:

```text
--config configs/semantic_v2/gate_c_v1.json
--execution-id <separately-approved-id>
--root <reviewed-checkout>
--approval-file <separately-reviewed-execution-approval.json>
```

- **Ordered workflow:** `preflight`, `collect`, `prepare`, `validate-dataset`; after separate fitting/calibration approval, `train`, `validate-model`, `calibrate`, `validate-readiness` for each explicit `--detector xgboost|random_forest`.
- **Profile:** `--profile pilot|baseline` on preflight and collect. All later operations inherit the collection's recorded profile.
- **Final checks:** `verify-preservation`, `compare-repeats --other-execution-id <other-id>`, `close-review --other-execution-id <other-id>`. A second independent execution requires its own scope-approved ID and all separately authorized stages.
- **Success/failure:** A completed command prints its immutable artifact path and exits zero. Missing/out-of-scope approval or expected validation/collision errors print a denial/failure and exit two; unexpected exceptions abort rather than marking success. No CLI command grants Gate D approval.

No execution-approval JSON is supplied. Its future fields must be `gate: "C"`, `approved_for_execution: true`, exact `config_digest`, explicit `execution_ids`, explicit `phases` and a nonempty `approval_reference`. Supplying a file is not itself human approval; the reference must point to an actual separate approval.

## Review evidence and limitations

- **Unit scope:** Literal expected-value vectors, online/offline equality, rollback, invalid attempts, malformed config/manifests, entity leakage, probability validation, policy arithmetic, profile/split restrictions, immutable storage, publish faults and approval denials. Neither random generation nor model fitting/calibration is exercised by new tests.
- **Legacy limitation:** The accepted `TestEnvironment.test_process_transaction` omits its timestamp and excludes the valid FLAG result. The Los Angeles-timezone failure reproduces on the untouched base; the assertion and behavior must not be weakened to hide it. Existing XGBoost serialization warning remains visible.
- **Execution unknowns:** Pilot runtime/memory/support, realized class balance, fitted model quality, new model serialization/reload, grid feasibility and end-to-end repeatability remain unverified. Generated data is synthetic; no operational fraud performance, real loss estimates or legacy-model semantic compatibility is certified.
- **Gate D:** Research validity, temporal/entity generalization claims, false-positive economics, ablations, paired multi-seed uncertainty and S1–S4 interpretation require a separately approved milestone. A closure candidate is not human acceptance or permission to research, publish or merge.

Stop at implementation review. Preserve original artifacts and accepted branch references, and request separate approval before any production preflight or pilot.
