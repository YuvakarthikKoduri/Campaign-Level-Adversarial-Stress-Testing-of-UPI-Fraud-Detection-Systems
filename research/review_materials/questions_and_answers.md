# Likely faculty questions

## Contribution and prior research

- **What is genuinely new?** The implemented package combines campaign stopping/ledger bookkeeping, five online-matched controls, synthetic mechanism lineage, benign-shift controls, independent reconstruction and a safe local workstation. The search does not establish that this combination is first; see the literature matrix.
- **Does RL fraud evasion already exist?** Yes. [Fraud-RLA](https://doi.org/10.1109/TDSC.2026.3673847) is close prior work, and [banking evasion studies](https://www.usenix.org/conference/raid2020/presentation/carminati) predate this project. Our tabular multi-transaction simulation is a different implementation, not invention of the field.
- **Why campaigns rather than only AUC?** Campaigns expose target completion, first intervention and gross ledger effects under resource limits. AUC ranks transactions on a specified sample; it does not describe the simulator's stopping/target endpoint.
- **How do we compare with publications?** Qualitatively by dataset, threat model, detector/attacker, unit and metrics. No common-data head-to-head experiment was executed, so published rates are not ranked against ours.

## Design and interpretation

- **Why static, rule-adaptive and RL?** Static/rule isolate the implemented explicit-feedback kernel; RL/blind RL probe explicit-label information; RL/zero-Q probe learned values under common online actions. Offline training cost is not equalized across all arms.
- **What is held out?** The new pilot excludes the declared GE generator ancestry and nontrivial matching prefixes from registered fit/validation/calibration data. Historical detector-family training exclusion is unverified; attacker holdout alone is not detector holdout.
- **Why do benign GE mimics get blocked?** Their declared mechanism and available features overlap the attack challenge; the records show high blocking. A causal feature-level explanation requires ablations or other new evidence, so do not assert one.
- **Does RL win?** Not universally. GE RL-minus-zero-Q is negative for XGBoost and positive for RF; results depend on task/detector/control. The exploratory intervals are unadjusted and there are only nine independent blocks.
- **What do the results prove?** They establish recorded synthetic outcomes, internal reproducibility and the specified lineage contract within the evidence. They do not prove real UPI effectiveness, all-unseen fraud detection, production readiness or victim money saved.
- **Are there 7,200 independent models?** No. There are nine independent blocks and eighteen fitted detector artifacts; contexts/policies share block structure. Repeats/reloads do not add independent blocks.
- **Is zero ordinary-benign BLOCK enough?** No. It is an observed finite-stratum result; the GE-mimic failure demonstrates a major distribution-shift limitation.

## Engineering, ethics and next steps

- **Can the dashboard run the program?** Yes. Fixed validated Python commands execute real short workflows, preserve stdout/stderr and exit codes, and safely cancel process groups. There is no unrestricted shell or Git/Gate C endpoint.
- **Why not production-ready?** Synthetic data, narrow mechanisms/features, high benign-shift blocking, pickle/platform constraints, no bank integration, no deployment validation and no internet-service hardening.
- **What failed during integration?** Initial nested-local-state log access was rejected; root ordering was fixed with a regression test. A verifier accepted reused evidence directories; it now rejects them. Initial paper compilation attempts failed and were corrected; logs remain in the verification record.
- **Are AI/plagiarism percentages below 10%?** Not measured. Both are pending approved external verification; this is an explicitly AI-assisted draft requiring human authorship/policy approval.
- **What remains next?** Human manuscript/venue/license approval and genuine checker reports for submission; separate approved research would be needed for real data, richer features, cost-matched training, broader mechanisms and powered lockbox validation. Gate C remains HOLD.
