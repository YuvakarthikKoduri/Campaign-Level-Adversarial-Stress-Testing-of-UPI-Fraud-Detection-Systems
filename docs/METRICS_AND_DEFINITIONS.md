# Metric dictionary and evidence contract

All project values below are raw or derived simulator quantities, not externally published financial outcomes. Experiment selection is mandatory: `mechanism-pilot-v1` and `legacy-corrected` are not interchangeable populations.

| Metric | Definition, units and denominator | Source / type | Supports; does not establish |
|---|---|---|---|
| Campaign completion | Completed/attempted campaigns; percent; target reached within contract | Pilot `campaigns.jsonl`: `success`, context target and gross paise; derived | Target attainment in simulator; not fraud prevalence or deployment success |
| Evaluated transactions | Count of scored transaction records, including final BLOCK | Campaign transaction arrays; raw count | Evaluated attempts; not necessarily settled transfers |
| ALLOW / FLAG / BLOCK | Counts by recorded decision; denominator all evaluated transactions when a fraction is requested | Per-transaction `decision`; raw | Simulator action outcomes; FLAG can still transfer, BLOCK stops |
| Gross simulated debit | Sum of actual `amount_transferred`, in INR; internally integer paise, no denominator | Transaction records and `gross_paise`; derived cross-check | Simulated source outflow; not victim loss, net loss or savings |
| Proposed blocked amount | Proposed amount on BLOCK rows, INR | Transaction proposal fields; derived if present | Rejected proposals only; not proven money saved |
| First BLOCK | Elapsed simulated seconds from context start to first BLOCK | Transaction timestamps; derived; report event count/all campaigns | Observed intervention timing; conditional mean is not uncensored survival estimate |
| First FLAG | Elapsed simulated seconds to first FLAG alone | Transaction timestamps; derive only when present, report count | Alert timing; not necessarily campaign stop |
| First alert | First FLAG-or-BLOCK elapsed seconds | Transactions; conditional mean with observed/all counts | Any-alert timing; distinct from first FLAG alone |
| Benign false-block | Benign episodes with peak score ≥ block threshold / benign episodes; percent | `benign_scores.json` plus block manifest thresholds; derived | Defined benign-stratum behavior; not population false-block rate |
| Any benign alert | Peak ≥ flag threshold / episodes; percent | Same scores/thresholds; derived | FLAG-or-BLOCK threshold crossing; not BLOCK-only |
| Block variability | SD of nine block-specific completion rates, percentage points | Matched campaign groups; derived | Between-block pilot variability; not confidence interval |
| Paired contrast | Mean within-block completion difference; percentage points | Common context IDs/blocks; derived | Descriptive policy contrast under this contract; not general causal superiority |
| AUC | Probability a positive receives a higher score than a negative under a specified labeled sample | Only valid with identified score/label population; not used as current headline | Ranking on that sample; not campaign completion or GE robustness. Historical AUC unverified |
| Independent blocks | Independent synthetic data/model/policy namespaces; count 9 full pilot | Config/manifests; raw design count | Replication unit; repeat/reload not extra blocks |
| Training episodes | Episodes used to update learned policies; full pilot 10,800 | Manifest and training transitions; recorded | Offline learning workload; not attack evaluation sample size |
| Evaluation campaigns | Full pilot 7,200, each block×detector×family×arm×context | Manifests and campaign rows; raw | Fixed synthetic task sample; not 7,200 independent models |
| Test cases | Distinct collected selected pytest cases, with pass/fail/error/skip/deselection counts | Current JUnit/log evidence; software evidence | Exercised behavior; not scientific or real-world validation |
| Reconstruction checks | Assertions of hashes, arithmetic, lineage and TD replay | Verifier JSONs; integrity evidence | Internal consistency; not additional tests/campaigns/replications |

For pilot totals inspect `results/independent_reconstruction.json`; for cell denominators/SD and timing event counts inspect `results/results_summary.csv`. The score strata have 3,600 test episodes per detector per stratum, while each attack cell has 360 campaigns across nine blocks. Calibration uses a different population and is not pooled into benign test rates.

Current figure uncertainty is between-block SD; contrast CSV intervals are unadjusted exploratory bootstrap intervals. Reproduction source digests identify every included main-run file. No real victim-loss measure exists in this project.
