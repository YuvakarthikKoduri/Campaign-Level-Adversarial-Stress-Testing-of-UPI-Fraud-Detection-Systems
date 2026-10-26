> HISTORICAL SCOPE RECORD: The body below retains earlier claims and workspace paths, not current acceptance. Use the [current README](../README.md), [verification report](VERIFICATION_REPORT.md) and [handover](HANDOVER.md) for present commands, counts and limitations. Historical completion/AUC/novelty/production claims are not adopted. Gate C remains HOLD.

# Corrected-v2 experiment contract

This contract applies only to new corrected-v2 runs. Historical results and existing serialized models are retained unchanged, and corrected runs must not be combined with historical tables.

## Threat model

- **Knowledge:** The primary attacker receives no detector architecture, parameters, threshold, exact score, feature vector, or internal transaction history through the simulator API.
- **Feedback:** `label_only` exposes the submitted source, beneficiary, amount, simulated timestamp, ALLOW/FLAG/BLOCK decision, execution status, and transferred amount; `score` additionally exposes the exact probability and is a distinct experimental condition.
- **Controls:** Policies choose amount, controlled source and eligible beneficiary; they can submit monotonic event times subject to the configured horizon, while built-in policies use family-specific timer schedules.
- **Bounds:** Finite positive transaction amounts must not exceed the configured per-transfer limit, remaining gross-transfer budget, or available active-account balance.
- **Universe:** Campaigns pre-register a closed, declared VPA/account pool with explicit initial balances; no policy-generated source or beneficiary outside that pool is admitted.
- **Validity:** Self-transfers, malformed/nonfinite amounts, backwards/aware timestamps in the naive-UTC clock, inactive account/VPA transfers, and undeclared accounts are invalid rather than fraud-detector blocks.
- **Boundary:** `AttackerCampaignView` is an immutable objective-only interface, and feedback is allowlisted; this is application-level information isolation, not an operating-system sandbox against malicious Python code.

The standalone environment retains convenience auto-registration for legacy demonstrations. Research campaigns cannot exploit it because the executor validates the closed pool before processing.

## Execution and financial metrics

ALLOW and FLAG both transfer money when the transaction is feasible, while BLOCK transfers zero. FLAG denotes detection/review without a simulated hold, and the first BLOCK terminates the campaign.

Ledger balances are conserved within the simulated account universe. Exposure is gross successfully transferred value, not net exfiltration or unrecovered financial loss, and no refunds, reversals, recovery, or financial-cost model is implemented.

- **Attempted amount:** Sum of amounts of valid recorded transaction attempts, including detector blocks.
- **Transferred exposure:** Sum of `amount_transferred` through campaign termination/cutoff.
- **Pre-detection exposure:** Gross value transferred strictly before the first FLAG/BLOCK event, excluding money transferred by that same FLAG event.
- **Pre-intervention exposure:** Gross value transferred strictly before the first BLOCK; the BLOCK event itself transfers zero.
- **Campaign success:** Gross transferred value meets/exceeds the predeclared target.
- **Detection:** First FLAG or BLOCK, measured in simulated seconds from campaign start.
- **Intervention:** First actual detector BLOCK, not merely flagging, invalidity, or horizon exhaustion.
- **Censoring:** An unobserved detection/intervention is `null` per campaign; counts are reported, and conditional mean times are explicitly among observed events only.
- **False positives:** Legitimate transaction FLAG/BLOCK rates and legitimate attempted amount prevented are reported when benign observations exist; absent benign traffic yields `null` rates, not a fabricated zero.

The `total_exposure_before_detection` and intervention counterparts use cutoff exposure when the event is unobserved. Read them together with censor counts; they are not uncensored time-to-event estimates.

`campaign_success_rate` is a descriptive rate across the supplied campaign collection. In mixed populations, use `fraud_campaign_success_rate` and its declared fraud-campaign denominator for attacker success.

## Termination and invalid runs

SUCCESS is target reached; BLOCKED is first detector block; TIMED_OUT is step or simulated-time horizon; FAILED is an attacker stop or budget exhaustion; INVALID is an invalid/infeasible action. Every normal executor exit has a terminal status, reason, and simulated cutoff.

Invalid campaigns invalidate the research runner rather than silently lowering success rates. Inference/schema/probability errors raise, the run manifest is marked failed, and no completed canonical artifact is emitted.

Invalid-action details remain diagnostic evidence, not attacker-visible scores or detector decisions. A failed run directory is retained and cannot be overwritten.

## Features and leakage

The strict ordered detector schema is `amount`, `hour_of_day`, `velocity_1h`, `is_new_vpa`. Unknown columns and nonfinite values are rejected.

- **Amount/hour:** Values from the action evaluated at its simulated event time.
- **Velocity:** Previously recorded attempts from the source VPA in `(event_time - 1 hour, event_time]`, excluding the current attempt; simultaneous earlier-processed attempts count.
- **New VPA:** First-observed source VPA before the current attempt, independent of pre-registration and ledger posting.
- **Prohibited inputs:** Campaign labels, family/scenario IDs, future outcomes, and post-decision feature mutations never enter the detector input mapping.

Research campaigns enforce chronological processing. The standalone feature-window calculation is also bounded against future events so that a malformed historical ordering cannot silently count them.

The existing synthetic CSV lacks full timestamps, entity identifiers, and campaign-family provenance. Its independent random row split does not support a claim of temporal/entity-held-out or strict leave-one-family-out detector validation.

Inspection of `rebuild_upi_baseline.py` shows training-only fitting, validation early stopping/calibration, and separate test evaluation. That code-path inspection does not establish the exact training provenance of the existing serialized artifacts; do not claim that original training partitions or environment have been recovered.

The new run manifest records development/evaluation intent and rejects overlap with declared development seeds. It cannot discover undisclosed previous human tuning or certify that an undeclared seed was never used.

## Pairing, adaptation, and reproducibility

Workloads are immutable and pre-generated independently of the detector, scenario execution order, and global random state. S1/S2 share known initial specifications, S3/S4 share unknown initial specifications, and both detectors share those same specifications.

Unknown-family quotas cycle through slow drain, gradual escalation, and beneficiary hopping, with counts differing by at most one. Seeds, policy/timer/VPA streams, target amounts, clock, and VPA strategy are persisted; comparisons share initial conditions, not forced post-feedback actions.

Each family is produced by the same policy class with adaptation explicitly enabled/disabled. Static gradual escalation follows a predeclared step-based ramp, while adaptive gradual escalation responds to feedback; source selection, initial amount, and initial random state match.

The original `StaticAttacker` remains available for legacy scripts, but corrected S1/S3 use the static mode of the same family policy as S2/S4. This is an intentional new baseline definition, not a numerical reproduction of the old static policy.

Safe-beneficiary sets are sorted before random selection to avoid Python hash-order dependence. Timers use cumulative bounded intervals and reset their seeded RNG when reset.

Loaded detector objects use one inference worker so tree-probability accumulation order is stable. This changes in-memory execution settings only; the original model bytes remain unchanged.

`canonical.json` contains semantic configuration, workload, campaign outcomes, traces, feedback, balances, and metrics. Run identity, actual wall-clock timestamps, Git state, package inventory, and performance timing are outside it; same configuration/code/artifacts should reproduce canonical bytes in the supported environment.

## Decision policy and artifact portability

The declared default three-way policy is ALLOW below 0.40, FLAG from 0.40 to below 0.70, and BLOCK from 0.70. Binary thresholds stored in the original models are recorded separately and are not silently substituted for a three-way policy.

No calibration on evaluation output occurs in this milestone. Research comparisons must later declare a validation-only operating-point selection protocol and benign false-positive budget.

`requirements-milestone1.lock` captures the tested Linux/Python 3.11 runtime and test dependencies. It is not the original training environment or a promise of pickle portability across platforms, and the existing XGBoost serialization warning remains visible because modifying model artifacts was prohibited.

## Acceptance boundary

Regression tests, paired smoke runs, canonical repeats, artifact hashes, and a clean-environment check support review of these repairs. They do not establish statistical superiority, real-world loss reduction, strict unseen-family generalization, original model provenance, or completion of future ablation/multi-seed studies.

Milestone acceptance remains subject to reviewer sign-off and explicit disposition of these provenance/generalization limitations. Do not begin research evaluation automatically.
