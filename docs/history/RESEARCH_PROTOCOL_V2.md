# UPI Fraud Stress Lab: Research Protocol v2

Status: **PROPOSED, NOT APPROVED FOR EXECUTION.** This protocol designs a prospective synthetic study; it does not implement or authorize it. The remediation candidate, research audit, prior models, datasets and results remain frozen. Gate C remains **HOLD**.

## Scope and rationale

The smallest defensible follow-up is one mechanism-level holdout study, two existing detector architectures retrained with bound provenance, and five action-matched attacker controls. It is not immediately a four-family leave-one-out benchmark, a new detector architecture, a dashboard, or a real-world UPI evaluation. The initial held-out mechanism is a precisely constrained gradual-escalation process; a high-value process supplies the in-training reference.

The audit motivates, but does not confirm, the proposed hypotheses. Its retained tables show static and rule-adaptive known-workload success of 100% for both models, other-workload rule improvements, a large known-workload trained-versus-zero-Q difference, and 100% other-workload success for both RL variants. It also identifies target clipping, amount/pacing differences, three policy-seed replicates, missing detector-family provenance and absent benign operating-point controls. References: frozen `upi-research-validity-audit-01/RESULT_TABLES.md:9–24` and `INDEPENDENT_RESEARCH_VALIDITY_AUDIT.md`, sections “Experimental pipeline,” “Static/adaptive fairness matrix” and “Metric and statistical audit.”

Those results belong to v1 and its remediation. Proposed v2 changes the experimental contract deliberately: all arms share legal actions and clipping, the family grammar is enforced for every actor, training data acquire mechanism-level lineage, and thresholds are calibrated on benign validation episodes. Do not pool v1 and v2 records or interpret their difference as a randomized treatment effect.

The proposed estimand is performance in a specified synthetic environment. “Held out” means excluded from detector fitting, detector/model selection, threshold calibration and RL training under the rules below; it does not mean unfamiliar to the researchers, outside all feature support, or novel to real fraud systems.

## Research questions and falsifiable hypotheses

The study has a provenance prerequisite, three primary policy contrasts, and a descriptive in-training reference. Its primary endpoint is campaign completion on the held-out gradual-escalation mechanism.

| Question | Falsifiable hypothesis / contrast | Interpretation limit |
|---|---|---|
| Was the held-out mechanism excluded? | No held-out mechanism or forbidden derivative appears in any detector-fit/model-selection/calibration or RL-training input | A necessary data-integrity prerequisite, not an outcome test |
| What does rule feedback change? | H1: completion probability differs between rule-adaptive R and its exact static neutral-feedback counterpart S | Effect of this specified feedback-driven rule, not adaptation in general |
| What does an explicit online decision label add to RL? | H2: completion differs between label-observing trained RL L and label-blind trained RL B | Effect of this observation-design intervention under a common training procedure |
| Does learning help beyond zero Q? | H3: completion differs between trained RL L and zero-Q control Z using the identical action builder | Effect of this learning procedure relative to random ties, not optimality |
| Does the result depend on workload? | Prespecified secondary contrast: each policy difference on held-out versus in-training mechanisms | Mechanism interaction in this synthetic design, not proof of all unseen-fraud generalization |

H1–H3 are two-sided, with null difference zero, evaluated separately for XGBoost and Random Forest: six primary tests. Improvement and deterioration are both reportable. The proposed smallest practically important difference is **five absolute percentage points in completion probability**, requiring researcher approval; it is a synthetic-project decision threshold, not a clinically or economically calibrated value.

A significant nonzero difference is distinct from a practically established difference. Claiming improvement requires the multiplicity-adjusted interval to exclude zero in the favorable direction; claiming an effect of at least five points requires its lower bound to exceed five points. Failure to reject zero does not establish equivalence.

## Detector data and artifact-bound provenance

Existing detector artifacts remain historical controls only. They cannot acquire missing lineage retrospectively by adding a metadata label. The prospective study must train fresh XGBoost and Random Forest artifacts on newly versioned synthetic episode corpora after separate implementation/execution approval.

The minimum data lineage is:

1. Define the episode mechanism, latent label, account roles, event clock, background assumptions, feature semantics and generator revision before producing data.
2. Allocate complete episodes to detector fit, model-selection validation, benign threshold calibration, pilot or final test before extracting features. Never split transactions from one episode across partitions.
3. Generate detector training episodes with a detector-independent legal-action sampler, not by keeping only transactions that an existing detector allows. Fit uses benign episodes and the in-training high-value mechanism only.
4. Compute all four features with the same causal, prior-history feature extractor planned for inference. The new-VPA feature must explicitly mean first prior outgoing use of the source in the declared history window, not an unrelated Bernoulli recipient-novelty proxy. Labels, mechanism IDs, split IDs and future events are never model inputs.
5. Fit preprocessing, imputation, resampling or class weights only from fitting data. Early stopping/model selection uses only the allowed validation partition. Freeze model settings before the pilot; no held-out-mechanism result selects hyperparameters.
6. Bind each saved model's bytes to exact input hashes, training IDs/split hashes, feature/preprocessing schema, allowed/excluded mechanism versions, code/environment identities, seed lineage and fit log.
7. Independently scan the actual inputs and forbidden ancestry closure; record zero forbidden inputs. Also scan episode signatures across all partitions to detect mislabeled mechanism duplicates, not merely IDs.

The held-out gradual-escalation generator, its parameter variants, prefixes and derived copies are prohibited from fit, model selection, calibration and RL training. A mechanism-signature match in any fitting/calibration episode, including a benign one, is quarantined and reviewed before fitting; it is not silently relabeled. This strict exclusion conditions the synthetic development population and must be reported. Shared scalar amounts or individual feature vectors alone are not forbidden: sequence/mechanism exclusion is not feature-support exclusion.

Final benign controls include ordinary benign episodes and a separately labeled, mechanism-matched benign escalation stratum. This distinguishes novel sequence appearance from the latent fraud label and exposes false alarms on similar legitimate behavior. Their mixture weights are fixed before test release; stratum-specific results remain visible. These held-out benign mimics are also excluded from fit and calibration under the strict signature rule.

Required records and rejection checks are specified in `PROVENANCE_AND_CONTROL_SPECIFICATION.md`. Hashes provide content binding and tamper detection, not authenticated proof of how a model was historically trained; independent observation/replay of fitting is needed for that stronger assertion.

## Campaign mechanisms and holdout rules

The primary study uses just two explicit mechanism versions. Beneficiary hopping and slow drain are deferred because adding them does not resolve the two blockers minimally, and recipient hopping is not directly visible to the current four-feature detector.

| Mechanism | Operational grammar proposed for every arm | Role |
|---|---|---|
| HVB-v2 | First nominal amount 15,000; later nominal amounts 8,000 or 15,000, subject to target clipping | Detector/RL in-training fraud; independent reference evaluation |
| GE-v2 | First nominal amount 1,000; subsequent bands are nondecreasing in 1,000→3,000→8,000→15,000 order; increase at most one band per proposal; allow no more than two consecutive proposals at a band before requiring an increase, unless already at the top | Excluded mechanism for detector/RL training and model selection |

The common environment enforces the grammar, not each attacker's interpretation of a family name. The final amount is clipped to the exact remaining target and is explicitly exempt from the nominal band/monotonicity restriction. A campaign stopped early by BLOCK is a censored prefix of its assigned grammar, not reclassified into another family. Record nominal action, legal mask, phase/repeat count, clipped amount and observed prefix.

Both mechanisms use the same target distribution, accounts, start-time distribution, pacing vocabulary, feedback interface, resource limits and stopping rules. Their intended difference is amount-sequence grammar, not a smaller unknown-workload target or different source rotation. For cross-mechanism reference contrasts, pair target/context draws while retaining distinct mechanism episode IDs. This narrows causal interpretation to the defined mechanism package.

The held-out mechanism choice is informed by exploratory v1 results and feature observability. It is not an undiscovered mechanism, and one holdout supports claims only for GE-v2 under this protocol. A separate approved extension would be needed for broader leave-one-family-out conclusions.

## Five matched attacker controls

| Arm | Policy definition | Offline learning | Online labels at action selection |
|---|---|---|---|
| S: static | Same rule kernel as R, but its decision input is always NEUTRAL. Highest legal amount band and slow pacing are the neutral priority | None | None |
| R: rule-adaptive | Same kernel, initialization and parameters as S. ALLOW selects highest legal band/fast; FLAG selects lowest legal band/slow; START/NEUTRAL selects highest legal/slow. Grammar overrides illegal requests consistently | None | Actual prior ALLOW/FLAG; BLOCK terminates |
| B: feedback-blind trained RL | Same learner, state encoding, actions, reward/update rules and training quota as L; decision-label state slot is replaced by NEUTRAL during both training and evaluation | Same quota as L | No explicit online decision label |
| L: trained RL | Tabular Q-learning with explicit prior public decision plus common own-progress/horizon information; phase constrains the common legal mask | Fixed training quota | Actual public label, not scores/features |
| Z: zero-Q | Identical state/action builder and seeded greedy tie-breaker to L, with an empty zero-default table; no Q updates | None | Labels may be received but cannot influence equal action values |

S is an explicit, reasonably strong open-loop priority baseline, not the old 25k policy. S and R differ only in the decision-input intervention; they share the exact rule kernel and all legality/rounding behavior. R is not optimized on final outcomes, and it is not renamed RL.

B is specifically **online-label-blind**, not detector-naive: both trained arms use the same detector-derived training reward for Q updates. It may infer progress and terminal execution failure from its own actions, as all arms can. During evaluation, rewards are logged by an external observer and are not supplied live to either policy; B must not receive a label through reward, a safe-beneficiary cache, diagnostic text, or a hidden state slot. H2 concerns the explicit decision-observation design, not absence of all detector information during training.

Use the same Q-state layout for L/B/Z: binned own progress, remaining-step fraction and a decision slot, retaining the audited finite-history approximation. B always uses the NEUTRAL decision code. Previous nominal band and phase/repeat count belong to the common legality kernel, not a family-specific Q-table namespace; action selection and nonterminal bootstrap maxima are restricted to the recorded legal actions. This avoids making every held-out state structurally unseen solely by adding its family identifier to the key. Record unseen-state frequency and training/evaluation state-action support in the pilot.

No detector score, architecture, threshold, internal feature vector, future event, true fraud label or private ledger state is an observation. The mask describes the attacker's own permitted plan and is available equally to all arms. The compressed state is not claimed to be Markov or to guarantee Q-learning convergence.

The proposal retains alpha 0.25, gamma 0.95, training epsilon 1→0.05 and frozen evaluation epsilon zero, with randomized ties from an independent policy stream. **300 training episodes per learned arm is a fixed-budget comparison proposal, not a claim of convergence.** No episode count is selected on final-test reward. A pilot ceiling/floor failure triggers a reviewed protocol revision, not an undisclosed training-budget increase.

Z is necessary but not sufficient as a learning comparator: S additionally checks whether learned performance exceeds a prespecified action-matched open-loop policy. That L–S comparison is secondary, not an unregistered replacement if a primary contrast disappoints.

## Common environment and outcome contract

The following values are proposed for approval, not changes to the frozen candidate:

- **Actions:** Eight nominal combinations: amount 1,000/3,000/8,000/15,000 × pace 300/1,200 simulated seconds. The mechanism-dependent legal mask is identical for all arms in the same task. Recipient rotation is removed from the primary vocabulary because it is not a direct detector feature.
- **Money and target:** Integer paise in experiment accounting with explicit conversion to detector numeric amounts; targets sampled uniformly in paise from 20,000.00 to 40,000.00 currency units, shared across mechanisms. All arms clip the last amount to the same remaining target.
- **Accounts and flow:** One synthetic compromised source and one fixed synthetic receiving sink, with source balance 500,000 and no sink-to-source transfers. Any unused simulator accounts are inert and identical across arms. This removes recirculation as an exposure confound without implying a real victim or financial account.
- **Resource limits:** At most 30 proposals, duration at most 86,400 simulated seconds, gross transfer budget equal to target. Limits include the same proposal/rejection conventions for every arm; independent cap pressure is not a primary question.
- **Time/history:** First proposal at a context start hour drawn uniformly from 0–23; no prior source history in the primary study. This remains an explicitly cold-start study, not a background-population validation. Subsequent intervals come only from the common action vocabulary.
- **Feedback:** Label-only own-action outcome and transferred amount. First BLOCK ends the campaign for all arms; FLAG transfers in full and causes no delayed review/recovery.
- **Success:** Target reached in exact minor units before first BLOCK, timeout, proposal horizon, budget rejection, invalid transition or actor stop. No transaction follows a terminal event; the completion bonus can occur only once.

Use the audited reward weights unchanged as a proposed common training objective: normalized transferred progress ×3, newly reached completion +2, BLOCK −1, FLAG −0.2 and evaluated-proposal effort −0.02, plus −0.5 for unsuccessful step-horizon exhaustion unless BLOCK already ended the campaign. Pre-execution rejection instead receives the terminal −1.02 penalty, not both that penalty and a second ordinary step reward. The completion bonus occurs once. Its units are artificial utility, not currency loss. Record realized reward for all arms using a passive common scorer, without giving evaluation reward to action selection.

Removing legacy overshoot, using common pacing and targets, enforcing family grammars and simplifying account roles are intentional v2 design changes. Approval of this document is not implementation authorization.

## Seeds and untouched evaluation lockbox

Use independently sampled root namespaces for detector-data generation/splitting, detector fitting, RL training, pilot workloads and final-test workloads. Do not derive RL training roots from evaluation roots. Exclude the old public seeds 101/202/303 and their recorded derived streams from the final lockbox; a new seed alone is not sufficient if the task instances are reused.

An independent replicate block contains a fresh detector-training corpus/split, paired XGBoost/RF fits, independently seeded L/B training runs and fresh paired evaluation contexts. Within a block, all five arms use identical immutable workload specifications; the two detector algorithms also share the block's data/split/context inventory. Between blocks, these inventories and seeds are disjoint. This samples joint model/policy/workload variability without pretending that two models double the number of independent blocks.

After pilot-only replication planning, freeze protocol, generator/schema, model hyperparameters, rules, reward, training budget, calibration method, analysis code and stopping criteria. An evaluator/custodian then creates a separate final bundle and a hash commitment outside the frozen candidate. Access is logged; researchers do not inspect final labels/results until the locked run. Seed commitments do not prove secrecy or prevent off-record inspection, so custody and access controls must be documented.

Pilot outcomes may determine only sample size/feasibility under the declared rule. If they cause policy, generator, reward or threshold-method changes, issue a new protocol version, discard the pilot from confirmation and create a fresh final lockbox. No optional peeking, favorable-seed selection, or post-test threshold tuning is allowed.

## Benign controls and threshold calibration

Train and select detectors using allowed fraud plus benign episodes; choose score thresholds from a separate benign calibration partition, not final fraud success or GE-v2 scores. Proposed nominal calibration targets are at most 0.5% benign episodes with any BLOCK and at most 2.5% with any FLAG-or-BLOCK, leaving margin below final acceptance budgets of 1% and 5%. The researcher must approve these operating targets and a realistic enough synthetic benign schedule.

Choose a predeclared conservative empirical quantile rule with deterministic handling of score ties and threshold ordering. If no nondegenerate ordered pair is feasible, calibration fails; do not silently install an all-ALLOW fallback. Record exact rule, counts, empirical rates and uncertainty. Feature-history generation must be identical to inference; threshold choice never receives forbidden mechanism data.

Final benign evaluation uses ordinary and held-out mechanism-matched benign strata. Report both separately and with the predeclared mixture; do not reweight after seeing results. Any claim of matched operating points requires uncertainty on final benign rates and a predeclared tolerance, proposed as at most 0.5 percentage points between algorithms for ordinary-benign BLOCK rates. Passing an upper rate budget alone does not prove equality of operating points.

Final false-alarm budgets should be assessed with cluster-aware one-sided intervals across independent fitted-model blocks. Report per-block counts/rates as well. If the final gate fails, attack-policy contrasts remain reportable at their actual thresholds, but detector robustness/ranking at the intended operating point fails. Do not discard such blocks or recalibrate on test.

## Metrics and statistical analysis

The primary response is binary target completion on GE-v2. Let \(Y_{r,d,a,f,i}\) denote completion for replicate block \(r\), detector \(d\), arm \(a\), mechanism \(f\) and paired context \(i\). For each planned contrast, calculate its within-block mean paired difference, then average block differences with equal weights.

The independent replication unit is the entire model/policy/workload block, not a transaction or an individual campaign under a shared policy. Report actual model, policy, block and episode counts separately. H1 also varies across fitted detectors and workload contexts even though its arms are not learned.

Use six prespecified primary paired contrasts: R–S, L–B and L–Z on GE-v2 for each detector. Control familywise type-I error at 0.05 with Holm adjustment. Report conservative simultaneous 95% Bonferroni intervals across those six contrasts, plus unadjusted estimates for transparency; the intervals may be more conservative than the Holm tests.

Plan inference with block-level paired estimators and a prospectively validated small-sample interval/test procedure. Cluster bootstrap intervals require enough independent blocks and bounded/degenerate-outcome handling; do not bootstrap campaigns alone. Before final lock, approve the concrete method, coverage/power checks on pilot-based scenarios and the minimum block count. If these cannot be justified, the outcome is exploratory rather than quietly substituting a favorable test.

| Secondary endpoint | Required definition and reporting |
|---|---|
| First BLOCK | Incidence by proposal 30/time cap, first-event step and simulated time, observed counts; completion is a competing endpoint |
| FLAG | Any FLAG, FLAG count/rate per evaluated proposal and first FLAG-or-BLOCK; FLAG is not prevented transfer |
| Gross flow \(G\) | Sum of transferred amounts including FLAG; also \(G/T\), target-capped completion progress |
| Pre-event flow | \(G_{\text{pre-BLOCK}}\) and \(G_{\text{pre-alert}}\), explicitly excluding the event proposal; separately report transferred amount on the first FLAG |
| Post-alert flow | Total flow after and including the first alert, reported only with event incidence and remaining horizon |
| Attempts/resources | Proposals, evaluated transactions, ALLOW/FLAG/BLOCK, pre-execution rejections, duration, termination reason and training/evaluation detector-query totals |
| Learning | Common reward, recorded TD updates, frozen evaluations at prespecified checkpoints if separately budgeted; no changing-epsilon training curve presented as a fixed-policy generalization curve |
| Benign performance | Episode-level any BLOCK and any FLAG-or-BLOCK by stratum, plus transaction rates as distinct denominators |

In the proposed one-source/no-return model, gross flow also equals that synthetic source's net debit. It still does not equal unrecovered real victim loss: settlement, ownership verification, recovery and operational interventions are not modeled. Do not call pre-alert gross flow “money at risk” without that definition.

Observed-only mean event times are descriptive, not the primary ranking metric. Show event incidence, completion and other terminal causes jointly; do not turn null event times into zero or treat successful completion as ordinary independent censoring. Secondary mechanism/reference and endpoint comparisons are prespecified but exploratory; if formal claims are sought, approve an additional multiplicity family before final release. No primary endpoint substitution after a ceiling result.

## Replication planning and resources

The old three-seed variance is motivation only: v2 changes actions, family grammars, detector training and thresholds. It is not an adequate variance estimate for v2 power.

The proposal is an authorized-in-the-future pilot with an initial nine independent blocks and 40 paired contexts per mechanism/arm/model. Nine follows an approximate 25% relative standard error for a normally distributed between-block SD, \(1/\sqrt{2(R-1)}\); it is a planning starting point, not a guarantee of adequate variance precision. Forty provides at most 2.5-point increments for a single-arm completion proportion, half the proposed five-point effect, and can be split into two context batches. Neither number is the final confirmatory sample size.

Pilot information must include paired discordance rates, between-block contrast variance, within-block Monte Carlo variance, ceiling/floor frequency, benign tail/threshold uncertainty, fitted-model variability, action-mask frequency, query/fit cost and failures. Use an upper uncertainty bound on contrast SD, not only its point estimate; continue planning or declare infeasibility when the pilot is too degenerate to estimate it.

Choose final blocks and contexts jointly so within-block simulation noise is no more than a proposed 25% of total contrast variance, while reaching at least 80% power for a five-point difference under the most conservative primary alpha allocation. Use the maximum required replication over all six contrasts or explicitly narrow the claims before lock. Obtain final finite-block power/coverage assessment; a normal approximation alone is not the acceptance calculation.

`RESOURCE_AND_REPLICATION_PLAN.md` gives the planning equation, conditional scenarios, exact workload formulas and staged stop gates. For illustration only, paired block SDs of 0.05/0.10/0.15/0.20 imply normal-approximation requirements of 13/49/109/194 blocks before finite-sample adjustment, using the six-test conservative allocation. These are not measured SDs or selected sample sizes.

The initial pilot would entail 18 detector fits, 10,800 L/B training campaigns and 7,200 attack evaluation campaigns, at most 540,000 attack detector queries with a 30-proposal cap. This excludes benign calibration/testing, detector-data generation and fitting; those may dominate. Wall time and memory must be measured in the approved pilot. No Computer-credit estimate or guaranteed runtime is offered.

## Acceptance criteria and failure conditions

Before any study execution, the researcher must approve the decisions at the end and freeze the complete protocol. After approval, the following are preregistered gates, not opportunities to tune the final results.

- **Provenance gate:** Zero forbidden mechanism/ancestry/episode overlaps; complete source/data/split/model/policy bindings; independently verified model-fit inputs. Failure blocks detector-held-out claims regardless of success percentages.
- **Matching gate:** Equal per-cell specs, legal masks, action mapping, clipping, resource limits and threshold policy across arms. Logs prove no live score/reward leakage into B or any evaluation learner updates. Failure invalidates the affected causal contrast.
- **Pilot feasibility gate:** Estimate the declared variance components and achievable primary precision; record whether final replication fits the approved resource ceiling. Ceiling/floor outcomes with negligible discordance block informative completion-effect testing unless a reviewed new protocol changes the task.
- **Operating-point gate:** Ordered, nonfallback thresholds; final benign uncertainty meets approved budgets/tolerance for any matched-operating-point claim. Failed rates are retained, not removed.
- **Numerical/execution gate:** Ledger conservation, exact clipping, terminal consistency, one completion reward, policy immutability, complete counts and reproducible replay. Invalid actions or infrastructure failures are recorded by cause; they are not detector BLOCKs.
- **Outcome gate:** Report all six primary estimates and adjusted inference even when unfavorable. A null/non-significant result is not a project failure. Material benefit, harm and inconclusive results use the predeclared effect/interval rules.
- **Lockbox gate:** No access/tuning breach, unapproved exclusions or post-test configuration changes. A breach means exploratory labeling and a new approved lockbox for confirmation.

For policy-caused invalid actions, count the campaign as noncompletion in intention-to-evaluate summaries and also report the defect; do not label it detector prevention. For external infrastructure failure, retain the record and rerun all arms on that exact context only under a prespecified documented repair/retry rule. Unresolved or differential missingness prevents a confirmatory claim; do not silently replace failed seeds.

## Claim-to-evidence disposition

| Claim | Current retained records | Proposed v2 test / required evidence |
|---|---|---|
| Reproducible synthetic stress testing | Supported with qualifications by existing replay/arithmetic evidence | New versioned end-to-end replay and all provenance/matching gates |
| GE-v2 excluded from detector fitting/selection/calibration | Not established for historical artifacts | New bound model inputs, strict signature/ancestry scan and independent verification |
| Rule adaptation changes completion | Descriptive old rule results only | R–S on common kernel/actions/resources with block-paired inference |
| Explicit online decision feedback benefits RL | Not isolated by old comparison | L–B with no live reward/diagnostic leakage |
| Learning improves over zero Q | Old known-workload advantage is exploratory | L–Z with prospective seeds, same builder and inference; compare S secondarily |
| Adaptation causes greater detectability generally | Blocked by current asymmetries; no current known-rule paradox | At most a result about the specified feedback intervention, mechanism and operating point |
| Exposure is victim loss | Not supported | Still not a v2 claim; simulated source debit and gross flow only |
| Real-world UPI robustness or Gate C readiness | Not supported | Outside this protocol entirely |

Existing records can support additional paired/family tables, action-frequency, overshoot and query-cost accounting without new experiments. They cannot supply missing model-fit lineage, an untouched lockbox, matched-action counterfactual outcomes, v2 benign operating points or v2 variance. Those require new, separately authorized data generation, implementation and experiments.

## Unresolved decisions requiring researcher approval

The following decisions remain open; no answer is inferred from the earlier remediation authorization.

1. Approve GE-v2 as the single initial holdout and HVB-v2 as its in-training reference, including the exact band/phase grammar and final-clipping exception.
2. Approve strict mechanism-signature exclusion across all development inputs, its conditioning of the benign population, and the separate held-out benign mimic stratum.
3. Approve five arms, the static/rule kernel, the definition of online-label-blind RL, and the limited interpretation of the six primary contrasts.
4. Approve v2 target/action/pacing/account/history settings, minor-unit accounting and the unchanged proposed reward weights. These are not legacy-v1 reproductions.
5. Approve five percentage points as the practically important effect, at least 80% power, the multiplicity plan and the concrete finite-block inference method.
6. Approve pilot starting precision criteria, pilot access boundaries, final replication-selection rule and a hard CPU/storage/query budget. Final confirmatory blocks/contexts and detector corpus sizes remain unset.
7. Approve ordinary/mimic benign generation and mixture, calibration rule/tie handling, nominal 0.5%/2.5% targets, final 1%/5% budgets and cross-model tolerance.
8. Designate lockbox custody and a provenance reviewer, approve independent seed namespaces and access records, and decide whether stronger externally authenticated run records are required.
9. Approve missingness/retry, infeasibility and protocol-revision rules, including whether full detector variability or a narrower fixed-fitted-detector estimand is affordable.
10. Separately authorize any future implementation or pilot. **This document authorizes neither. Current candidate and audit evidence stay frozen; scientific conclusions remain limited to existing evidence; Gate C remains HOLD.**
