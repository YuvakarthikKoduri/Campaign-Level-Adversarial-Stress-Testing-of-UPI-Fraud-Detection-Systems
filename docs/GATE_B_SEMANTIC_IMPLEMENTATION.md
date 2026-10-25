# Gate B semantic feature implementation

This is an explicit, fixture-only implementation of the approved `upi_source_attempt_features/2.0.0` contract. The legacy runner, simulator, detectors, training scripts, datasets, and models remain unchanged; none is silently switched to this path.

## Contract

- **Source novelty:** First prior admitted source observation within the namespace, calculated before the current event. Registration, beneficiary-only appearances, and account aliases do not combine source histories.
- **Velocity:** Prior successfully processed/scored attempts from the exact source, regardless of ALLOW/FLAG/BLOCK, in `(t−3600 seconds, t]`. The current attempt and later sequences at the same timestamp are excluded.
- **Time:** Integer UTC microseconds and UTC hour. String input requires RFC 3339 with an offset and at most six fractional digits; ambiguous or lossy inputs are rejected. Only the explicit legacy bridge permits naive ISO timestamps interpreted as UTC.
- **Order:** Nondecreasing time and strictly increasing integer sequence, with duplicate IDs rejected within the namespace. Sequence numbers become observations only on successful publication; invalid ordinary actions do not consume them.
- **Admission:** Native `process_event` accepts immutable canonical actions and checks registered pools, active VPAs/accounts, exact-paise funds, and receiver balance limits before extracting/scoring. Same-account transfers through aliases are ineligible.
- **Bounds:** Amount and account balances are bounded to 1,000,000,000,000 paise; schema metadata records the amount bound. This is a declared simulation limit, not a payment-network limit.
- **History:** Fresh cold-start state per campaign, with source lifetime counters/identity sets and a one-hour recent queue. Compaction removes old queue entries, never lifetime novelty or duplicate protection.
- **Snapshots:** Canonical JSON with schema/contract/namespace/hash checks and structural checks on identities, counters, ordering, cutoff, and recent-window membership. A hash is integrity metadata, not an authenticity signature; callers must trust snapshot origin and validate the first scored position.
- **Vector:** `amount`, `hour_of_day`, `velocity_1h`, `is_new_vpa`, encoded by the shared encoder as a read-only `(1, 4)` float64 matrix. Integer-paise canonicalization prevents arbitrary fractional-paise feature rows.

## API boundaries

The native online entry point is `SemanticEnvironment.process_event(FeatureEvent(...))`. Accounts and VPAs must be initialized explicitly before processing; there is no convenience auto-registration.

The offline entry point is `replay_events(admitted_events, namespace, snapshot=...)`. It accepts a canonical log prefix known to have completed successful admission/processing, not unvalidated candidate actions, settlement-only records, or labels. It calls the same extractor, encoder, history-view, and observation-commit interfaces used online.

The replay adapter does not infer admission from a fraud label or model decision. Any future dataset importer must validate logged admission provenance separately; that importer and bulk preparation are Gate C work.

`encode_rows` and `decode_rows` are in-memory fixture codecs with event mapping, sequence, and current extractor/schema metadata. They do not write datasets or create artifact directories, and they are not a complete dataset/model provenance chain.

`feature_metadata` hashes the four feature implementation modules and records contract/schema digests. The read-only split validator checks explicit train/validation/test membership and prohibited group overlap; it does not select splits or establish empirical generalization.

## Atomic processing

The semantic adapter reuses the existing entity/setup/read API but stages all processing changes in an isolated ledger state. Exact integer-paise balances are authoritative; inherited float balances are compatibility views checked before admission.

The path validates action/history and ledger feasibility, extracts/encodes, obtains a fixture score, applies the existing threshold policy, stages settlement and diagnostics, commits the observation in staged history, checks conservation/invariants, and publishes by one state-reference swap. ALLOW and FLAG transfer; BLOCK transfers zero but commits an observation.

An inference, ordering, schema, internal settlement, history, response, or pre-publication exception invalidates the run and leaves the previous state reference intact. No retries or continuation of an invalidated environment are permitted. Ordinary infeasible actions return an invalid response without scoring, ledger writes, diagnostic appends, or history changes.

This is a single-writer, in-process simulator contract, not a crash-durable database or a multi-threaded transaction manager. Reentrant processing is rejected, and predictor/external callback side effects are not rolled back; fixture predictors must be pure.

Current state is obtained through the environment. Previously returned mutable Account/list references represent older staged-state snapshots after a successful event; they must not be cached as live write handles. Direct external balance mutation is detected as ledger corruption; the API is not a security boundary against arbitrary in-process code.

`SemanticCampaignExecutor` is an opt-in bridge to the actual existing campaign loop. It requires a fresh matching namespace/environment, explicit legacy-UTC interpretation, the same fixture detector, and one invocation per environment; it preserves label-only feedback by default and first-BLOCK termination.

Unexpected executor/feedback exceptions restore the complete pre-call semantic ledger/history and campaign accounting, mark the run invalid, and propagate. Prior callback side effects remain outside rollback scope and cannot be counted as valid evidence. A normal INVALID campaign is also marked invalid and cannot resume.

The direct environment primitive permits a subsequent attempt after a BLOCK for history-unit testing; the actual campaign loop does not. This separation does not change the Milestone 1 lifecycle policy.

## Fixture detector restriction

`FixtureDetector` is deliberately the only accepted semantic online predictor in Gate B. It validates feature metadata, vector shape/dtype, and finite probability range, and clearly advertises `fixture_only=True`.

It has no artifact loader, training, calibration, or legacy fallback. Test-double scores use the unchanged development threshold defaults; they are not trained-model measurements or certified operating points.

The new path is not selectable in `run_experiment.py` or the legacy scenario configuration. Explicit production-model adapters, dataset/model lineage manifests, artifact collision checks/writers, and runnable preparation/training remain separately authorized Gate C work.

## Validation commands

Use the existing pinned Milestone 1 environment; no new dependency is required. There is no model fitting, dataset creation, or research evaluation command in this implementation.

```bash
python -m pytest tests/test_gate_b.py -v
python -m pytest tests test_timing.py test_vpa_strategies.py \
  examples/test_environment.py test_families.py -v
```

The explicit second command matters because the repository's pytest configuration defaults to `tests/`, excluding 19 existing root/example cases. Existing legacy-model portability warnings remain visible.

A stress check also reproduced a pre-existing legacy test limitation on the unchanged repair commit: `TestEnvironment.test_process_transaction` omits a timestamp, reads wall-clock hour, and accepts only ALLOW/BLOCK even though FLAG is a valid outcome. At the recorded Los Angeles local hour it fails on both baseline and this branch; this test and legacy behavior are intentionally not changed. Treat the recorded full-suite results as environment-specific, not a claim that all legacy tests are timezone/clock invariant.

Independent expected-value assertions cover first use, source/beneficiary roles, exact window boundaries, simultaneous ordering, retention, reset, alias behavior, and clock normalization. Integration checks cover real online/offline vector parity, shared-call-path spies, serialization/metadata rejection, corrupt snapshots, pre-admission rejection, all three decision histories, staged faults, reentrancy, real executor feedback, first-BLOCK termination, and executor-wide exception rollback.

## Review boundary

Gate B does not establish that the preserved models were trained using the new contract. Original-model semantic parity/provenance and broader portability remain unresolved/deferred according to the prior review decision; no legacy artifact is relabelled.

Review the local diff, test logs, preservation checks, and limitations before authorizing anything else. Gate C data generation/training, Gate D research evaluation, publishing, and merging each remain excluded without separate explicit approval.
