# UPI Fraud Stress Lab

**Campaign-Level Adversarial Stress Testing of UPI Fraud Detection Systems**

## Corrected-v2 local repair status

The correctness/reproducibility repairs are awaiting review, not a claim of
production readiness or completed research evaluation. Read
[the corrected-v2 contract](docs/MILESTONE1_CONTRACT.md) before interpreting results.

New runs use paired immutable workloads, explicit simulated time, label-only
feedback by default, and fresh output directories. FLAG transfers count as
transferred exposure, invalid inputs are not detector blocks, and unobserved
detection/intervention times are censored rather than zero.

The tested runtime is Python 3.11 on Linux. The dedicated lock installs the
execution/test dependencies without retraining or modifying existing models:

```bash
python3.11 -m venv .venv-m1
. .venv-m1/bin/activate
python -m pip install -r requirements-milestone1.lock
python -m pytest . -v
python run_experiment.py --scenario all --detector both \
  --campaigns 6 --seed 999 --max-steps 30 \
  --output-dir results/runs --run-id paired-review-a
```

A repeated run ID raises instead of overwriting. For repeatability use another
run ID with identical semantic flags and compare `canonical.json`; manifests
intentionally differ in actual timestamps and run identity.

The existing XGBoost pickle emits a portability warning, which is not hidden.
No original training environment, temporal/entity-held-out validation, or strict
leave-one-family-out detector provenance has been established.

## Legacy documentation and historical examples

The sections below retain the original research narrative and historical numbers
for context. They are not corrected-v2 results, the original “85% complete” and
“29/29” claims are not current acceptance evidence, and the old unrestricted
dependency instructions are not the supported reproducibility lock.

## Overview

This project evaluates the resilience of fraud detection systems under UPI-specific campaign-level scenarios involving previously unseen and strategically adaptive fraud behavior.

Historical status claim: 85% complete. Current status is correctness repairs under review, with scientific evaluation still pending.

## Key Features

- ✅ **2 Baseline Detectors**: XGBoost (96.7% AUC) and Random Forest (96.3% AUC)
- ✅ **4 Campaign Families**: HIGH_VALUE_BURST, SLOW_DRAIN, GRADUAL_ESCALATION, BENEFICIARY_HOPPING
- ✅ **4 VPA Strategies**: Configurable source-VPA behavior for realistic velocity patterns
- ✅ **3 Attacker Types**: Static, Adaptive, Family-based (GradualEscalation, BeneficiaryHopping)
- ✅ **4 Scenarios**: S1-S4 (Known/Unknown × Static/Adaptive)
- ✅ **Realistic Timing**: Campaign family-specific transaction timing models
- ✅ **Campaign-Level Metrics**: Financial exposure, success rates, detection time
- ✅ **Full Test Suite**: 29/29 tests passing (21 core + 8 VPA validation)
- ✅ **Complete Documentation**: Validation reports for all major components

## Quick Start

### 1. Clone and Setup

```bash
# Clone repository
git clone https://github.com/YuvakarthikKoduri/Campaign-Level-Adversarial-Stress-Testing-of-UPI-Fraud-Detection-Systems.git
cd Campaign-Level-Adversarial-Stress-Testing-of-UPI-Fraud-Detection-Systems

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Verify Setup

```bash
# Run test suite (should show 21/21 passing)
pytest tests/test_core.py -v

# Run VPA strategy tests (should show 8/8 passing)
python test_vpa_strategies.py

# Run timing validation tests
python test_timing.py
```

**See [TEST_RUN_REPORT.md](TEST_RUN_REPORT.md) for a complete validated test run with detailed results.**

### 3. Run Experiments

```bash
# Run single scenario
python run_experiment.py --scenario S1 --detector xgboost --num_campaigns 30

# Run all scenarios for one detector
python run_experiment.py --detector xgboost --all

# Run all scenarios for both detectors
python run_experiment.py --detector xgboost --all
python run_experiment.py --detector random_forest --all

# Results saved to: results/xgboost/ and results/random_forest/
```

### 4. Explore Campaign Families

```bash
# Test all campaign families
python test_families.py

# See realistic timing behavior
python test_timing.py
```

## What's Included

### Pre-trained Models
- `models/baseline_xgboost.pkl` (149 KB, 96.7% AUC)
- `models/baseline_random_forest.pkl` (6.3 MB, 96.3% AUC)

### Dataset
- `data/synthetic/upi_transactions_v1.csv` (1.3 MB, 50,000 transactions)
- Realistic fraud/legitimate overlap (₹500-97K)
- Features: amount, hour_of_day, velocity_1h, is_weekend

### Source Code
```
src/
├── data/              # Data generation and processing
├── detectors/         # Fraud detector implementations
├── environment/       # UPI transaction simulator
├── campaigns/         # Campaign generator with timing and VPA strategies
├── attackers/         # Static, Adaptive, and Family-based attackers
├── experiments/       # S1-S4 scenario runner
└── visualization/     # Metrics and result analysis
```

### Scripts
- `run_experiment.py` - Main experiment runner (S1-S4)
- `prepare_data.py` - Generate synthetic UPI transaction dataset
- `train_upi_model.py` - Train XGBoost detector
- `train_random_forest.py` - Train Random Forest detector
- `test_families.py` - Validate campaign family behavior
- `test_timing.py` - Validate realistic timing implementation
- `test_vpa_strategies.py` - Validate VPA strategy framework

### Documentation
- `README.md` - This file (getting started guide)
- `FINAL_VALIDATION_REPORT.md` - Complete validation summary (85% completion)
- `SOURCE_VPA_STRATEGY_VALIDATION.md` - VPA strategy validation report
- `REALISTIC_VELOCITY_VALIDATION.md` - Timing and velocity validation
- `UPI_BASELINE_VALIDATION.md` - Detector baseline validation
- `REPRODUCIBILITY_GUIDE.md` - Full reproducibility instructions
- `DATASET.md` - Dataset documentation

## Core Research Question

> Can an existing fraud detector remain effective when an attacker uses previously unseen fraud behavior and changes its strategy based on the detector's responses?

**Answer**: Depends on the scenario.
- **S1 (Known + Static)**: Both detectors fail (100% attacker success)
- **S2 (Known + Adaptive)**: XGBoost still vulnerable (96.7% success), Random Forest better (86.7%)
- **S3 (Unknown + Static)**: Both catch most fraud (6.7-13.3% success)
- **S4 (Unknown + Adaptive)**: Both fully effective (0% attacker success)

## Architecture

```
Dataset → Detector → Environment → Campaign → Attacker → Adaptation → Metrics
```

**Campaign Flow**:
1. **Campaign Generator** creates fraud campaign with family, timing model, and VPA strategy
2. **Attacker** chooses transactions based on strategy (static/adaptive/family-based)
3. **Environment** processes transactions and calculates features (velocity, etc.)
4. **Detector** evaluates each transaction and returns risk score + decision
5. **Attacker** observes feedback and adapts (if adaptive)
6. **Metrics** track campaign-level outcomes (exposure, success rate, detection time)

## Campaign Families

### 1. HIGH_VALUE_BURST
- **Behavior**: Large amounts, fast succession (2-5 min intervals)
- **Timing Model**: Poisson-distributed intervals
- **Use Case**: Compromised account, immediate extraction

### 2. SLOW_DRAIN
- **Behavior**: Moderate amounts, slow pace (30-60 min intervals)
- **Timing Model**: Gaussian intervals with drift
- **Use Case**: Avoiding velocity-based detection

### 3. GRADUAL_ESCALATION
- **Behavior**: Start small (₹500), increase 30% on success
- **Timing Model**: 10-20 min intervals
- **Attacker**: GradualEscalationAttacker (family-based)

### 4. BENEFICIARY_HOPPING
- **Behavior**: Rotate beneficiaries, limit reuse
- **Timing Model**: 3-8 min intervals
- **Attacker**: BeneficiaryHoppingAttacker (family-based)

## VPA Strategies

### 1. SINGLE_COMPROMISED_VPA
- One source VPA for all transactions
- **Velocity**: Highest (mean 0.82, max 3)
- **Use**: S1, S2 (Known fraud)

### 2. MIXED_REUSE
- 70% primary VPA, 30% rotation
- **Velocity**: Second-highest (mean 0.67, max 4)
- **Use**: S3, S4 (Unknown fraud)

### 3. SMALL_VPA_POOL
- Rotate through 2-3 VPAs
- **Velocity**: Low (mean 0.26, max 1)
- **Use**: Coordinated fraud rings

### 4. VPA_ROTATION
- Random selection from large pool
- **Velocity**: Zero (mean 0.00)
- **Use**: Baseline comparison

## Experimental Scenarios

| Scenario | Fraud Type | Attacker | Campaign Families | Expected Outcome |
|----------|------------|----------|-------------------|------------------|
| **S1** | Known | Static | HIGH_VALUE_BURST, COORDINATED_STRIKE | High success (matches training) |
| **S2** | Known | Adaptive | HIGH_VALUE_BURST, COORDINATED_STRIKE | High success + learning |
| **S3** | Unknown | Static | SLOW_DRAIN, GRADUAL_ESCALATION, BENEFICIARY_HOPPING | Low success (unseen patterns) |
| **S4** | Unknown | Adaptive | SLOW_DRAIN, GRADUAL_ESCALATION, BENEFICIARY_HOPPING | Lowest success (unseen + blocked) |

## Test Coverage

### Core Tests (21 tests)
```
tests/test_core.py:
✓ TestDetectorLoading (3 tests)
✓ TestCampaignGeneration (3 tests)
✓ TestAttackerBehavior (4 tests)
✓ TestEnvironment (3 tests)
✓ TestCampaignExecution (2 tests)
✓ TestMetrics (2 tests)
✓ TestReproducibility (1 test)
✓ TestEdgeCases (3 tests)
```

### VPA Strategy Tests (8 tests)
```
test_vpa_strategies.py:
✓ SINGLE_COMPROMISED_VPA uses one source
✓ SMALL_VPA_POOL uses 2-3 sources
✓ VPA_ROTATION preserves diversity
✓ MIXED_REUSE shows reuse + rotation
✓ Velocity emerges from reuse
✓ Velocity varies by strategy
✓ Campaign isolation preserved
✓ Seed reproducibility confirmed
```

## Advanced Usage

### Custom Campaigns

```python
from src.campaigns.generator import CampaignGenerator
from src.campaigns.vpa_strategy import VPAStrategy
from src.campaigns.timing import CampaignFamily

generator = CampaignGenerator()

# Create custom campaign
campaign = generator.create_known_fraud_campaign(
    target_amount=50000,
    vpa_strategy=VPAStrategy.SINGLE_COMPROMISED_VPA,
    family=CampaignFamily.HIGH_VALUE_BURST
)
```

### Running with Custom Seed

```python
from src.experiments.scenarios import run_scenario

# Reproducible results
results = run_scenario(
    scenario="S1",
    detector_type="xgboost",
    num_campaigns=30,
    seed=42  # Same seed = same results
)
```

### Analyzing Results

```python
import json

# Load experiment results
with open('results/xgboost/s1_results.json') as f:
    results = json.load(f)

print(f"Success rate: {results['metrics']['success_rate']:.1%}")
print(f"Avg exposure: ₹{results['metrics']['avg_financial_exposure']:,.0f}")
print(f"Total campaigns: {results['metrics']['total_campaigns']}")
```

## Regenerating Data and Models

If you want to regenerate from scratch:

```bash
# 1. Generate new synthetic dataset
python prepare_data.py

# 2. Train XGBoost detector
python train_upi_model.py

# 3. Train Random Forest detector
python train_random_forest.py

# 4. Validate detectors
python rebuild_upi_baseline.py

# 5. Run experiments
python run_experiment.py --all
```

## Requirements

- Python 3.8+
- pandas, numpy, scikit-learn
- xgboost
- pytest (for testing)

See `requirements.txt` for full dependency list.

## Known Limitations

### Campaign Velocity vs Training Velocity
- Campaign velocity: mean 0.67-0.82 (individual episodes)
- Training velocity: mean 3.76 (population aggregates)
- Gap is expected due to temporal scale differences

### Not Implemented
- RL-based adversarial agents
- GNN/LSTM detectors
- Campaign-aware detection
- Large-scale statistical validation (1000+ campaigns)
- Production features (APIs, dashboards, real-time monitoring)

These are enhancement opportunities, not core deficiencies.

## Validation Reports

- **FINAL_VALIDATION_REPORT.md**: Complete system validation at 85% completion
- **SOURCE_VPA_STRATEGY_VALIDATION.md**: VPA strategy framework validation
- **REALISTIC_VELOCITY_VALIDATION.md**: Campaign timing and velocity validation
- **UPI_BASELINE_VALIDATION.md**: Detector baseline performance validation
- **REPRODUCIBILITY_GUIDE.md**: Step-by-step reproducibility instructions

## Citation

If you use this work, please cite:

```
UPI Fraud Stress Lab: Campaign-Level Adversarial Stress Testing
of UPI Fraud Detection Systems (2026)
```

## License

Research prototype - not for production use.

---

**Status**: ✅ 85% Complete | 29/29 Tests Passing | Ready for Research Use

For questions or issues, see the validation reports in the repository root.
