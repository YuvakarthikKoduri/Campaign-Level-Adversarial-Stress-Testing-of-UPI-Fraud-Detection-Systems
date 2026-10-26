# Results and interpretation

The full retained pilot has 7,200 attack campaigns, 3,539 completed, 28,895 transactions, 24,634 ALLOW, 600 FLAG, 3,661 BLOCK and INR 192,300,996.32 gross simulated debit. These are independently reconstructed from raw main-run records; repeat/reload copies are not pooled.

| Detector / family | Static % | Rule % | RL % | Blind RL % | Zero Q % |
|---|---:|---:|---:|---:|---:|
| XGBoost / HVB | 3.611 | 3.333 | 3.333 | 4.444 | 4.167 |
| XGBoost / GE | 1.667 | 75.278 | 43.333 | 42.222 | 50.833 |
| RF / HVB | 58.333 | 56.667 | 74.444 | 75.278 | 48.056 |
| RF / GE | 71.111 | 100.000 | 91.944 | 89.722 | 85.278 |

Each cell is 360 campaigns in nine independent blocks. HVB is allowed in detector development; GE is the declared excluded synthetic mechanism. Full cell counts and block SDs are in [results_summary.csv](../results/results_summary.csv).

Legitimate GE mimics are blocked in 1,738/3,600 XGBoost episodes and 461/3,600 RF episodes, or 48.278% and 12.806%. Both detectors have zero observed ordinary-benign BLOCK; distribution shift therefore changes the observed operating behavior substantially. These two strata must not be combined to advertise a low false-positive rate.

Rule feedback improves GE completion for the implemented matched kernel, whereas RL-minus-zero-Q is negative for XGBoost and positive for RF. The paired contrast CSV supplies exploratory block intervals. There is no unqualified RL advantage, adaptation paradox, or general held-out fraud success.

The separate legacy study has 1,152 campaigns/4,161 transactions/three seeds, and known-workload static/rule completion is 100% for both detectors. Its historical detector ancestry and comparison asymmetries prevent stronger interpretation. Historical “unknown” refers to attacker-training exclusion, not demonstrated detector-family exclusion.

Short integrated demonstrations are software/reproduction evidence, not replacements for these full-run tables. Read `docs/VERIFICATION_REPORT.md` to identify newly run jobs and prior retained results.
