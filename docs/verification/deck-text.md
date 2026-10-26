<!-- Slide number: 1 -->
UPI Fraud Stress Lab
Campaign-level evaluation before intervention
An auditable engineering case study, not a deployed UPI detector.
Working software, matched synthetic controls and preserved adverse results.
Academic review draft • author, venue and external checker approval pending
Project records: results/ and docs/VERIFICATION_REPORT.md
SYNTHETIC RESEARCH  /  GATE C HOLD
1

<!-- Slide number: 2 -->
Why evaluate a campaign?
Transaction score
Campaign endpoint
AUC ranks examples in a specified dataset.
It does not say when a sequence stops.
Does a simulated actor reach its target before BLOCK?
FLAG can still transfer; BLOCK terminates.
Gross simulated debit is not victim loss or proven savings.
Project records: results/ and docs/VERIFICATION_REPORT.md
SYNTHETIC RESEARCH  /  GATE C HOLD
2

<!-- Slide number: 3 -->
The implemented evidence pipeline

→
→
→
Local dashboard
Safe Python runner
Existing engines
Immutable records
Independent checkers and raw-record reconstruction feed tables, figures and the paper.
No arbitrary shell, public binding or Git/Gate C endpoint.
Project records: results/ and docs/VERIFICATION_REPORT.md
SYNTHETIC RESEARCH  /  GATE C HOLD
3

<!-- Slide number: 4 -->
A narrow, registered exploratory pilot
Data and detectors
Five online-matched controls
9 independent blocks; 18 fresh detector fits.
HVB allowed; declared GE excluded from registered development data.
Ordinary benign and GE-mimic test strata.
Static; rule-adaptive; trained RL;
explicit-label-blind RL; zero Q.
Common actions, clipping, pacing and budgets.
Offline training costs remain unequal.
No powered confirmatory lockbox and no real-world UPI validation.
Project records: results/ and docs/VERIFICATION_REPORT.md
SYNTHETIC RESEARCH  /  GATE C HOLD
4

<!-- Slide number: 5 -->
Completion depends on detector and control

### Chart

| Category | XGBoost | Random Forest |
|---|---|---|
| Static | 1.6666666666666667 | 71.11111111111111 |
| Rule | 75.27777777777777 | 100.0 |
| RL | 43.333333333333336 | 91.94444444444444 |
| Blind RL | 42.22222222222222 | 89.72222222222223 |
| Zero Q | 50.833333333333336 | 85.27777777777777 |Held-out GE
360 campaigns per arm/detector
9 independent blocks
Block SD (percentage points)
Arm: XGB / RF
Static: 1.25 / 7.61
Rule: 14.33 / 0.00
RL: 24.08 / 8.36
Blind RL: 24.86 / 9.56
Zero Q: 17.98 / 6.43
Project records: results/ and docs/VERIFICATION_REPORT.md
SYNTHETIC RESEARCH  /  GATE C HOLD
5

<!-- Slide number: 6 -->
Benign mechanism shift is a major failure

### Chart

| Category | Legitimate GE mimics |
|---|---|
| XGBoost | 48.27777777777778 |
| Random Forest | 12.805555555555555 |48.278%
1,738 / 3,600 XGBoost episodes

12.806%
461 / 3,600 RF episodes
Ordinary benign: 0 observed BLOCK / 3,600 per detector.
No population guarantee; nine blocks. Mechanism exclusion ≠ reliable discrimination.
Project records: results/ and docs/VERIFICATION_REPORT.md
SYNTHETIC RESEARCH  /  GATE C HOLD
6

<!-- Slide number: 7 -->
What we can defensibly contribute
Prior research already does
Implemented contribution
Sequence fraud detection, synthetic finance,
banking evasion and learned attackers.
This project is not the first RL fraud attack.
Auditable campaign/ledger infrastructure,
five matched controls, narrow lineage checks,
benign-shift controls and reconstruction.
No universal superiority claim.
Fraud-RLA
Banking evasion
PaySim
Source: verified literature links below; project implementation and retained results
SYNTHETIC RESEARCH  /  GATE C HOLD
7

<!-- Slide number: 8 -->
A real local research workstation

![dashboard.png](Picture5.jpg)
Live faculty demonstration

Start a short actual job
Read stdout/stderr and exit code
Inspect a campaign sequence
Compare compatible results
Export CSV, Markdown and SVG
Project records: results/ and docs/VERIFICATION_REPORT.md
SYNTHETIC RESEARCH  /  GATE C HOLD
8

<!-- Slide number: 9 -->
Verified engineering; bounded scientific claims
Executed verification
Still requires human action
478 distinct tests passed in fresh Python 3.11.
Short legacy/pilot main, repeat, reload and check.
1,012,673 retained-pilot verifier checks;
30,985 TD updates replayed.
Approve authors, venue and AI-use policy.
Obtain genuine approved AI/similarity reports.
Select a project license.
Do not infer real-world effectiveness.
Ready for exploratory academic review, not unqualified submission.
Scientific validity extends only as far as the evidence. Gate C remains HOLD.
Project records: results/ and docs/VERIFICATION_REPORT.md
SYNTHETIC RESEARCH  /  GATE C HOLD
9
