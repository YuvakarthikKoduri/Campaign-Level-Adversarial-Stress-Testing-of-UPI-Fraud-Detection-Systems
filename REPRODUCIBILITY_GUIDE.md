> HISTORICAL SCOPE RECORD: The body below retains earlier claims and workspace paths, not current acceptance. Use the [current README](README.md), [verification report](docs/VERIFICATION_REPORT.md) and [handover](docs/HANDOVER.md) for present commands, counts and limitations. Historical completion/AUC/novelty/production claims are not adopted. Gate C remains HOLD.

# Reproducibility Guide

## Historical command guide

These older commands are not the current verified execution contract and
must not be interpreted as authorization to run every historical workflow.
Use `../HANDOVER.md` for the safe selected tests, legacy short demonstration
and separate new pilot/repeat/reload/checker commands. Old and new source
manifests are version-specific. Do not run Gate C; it remains HOLD.

This guide explains how to reproduce all experiments in the UPI Fraud Stress Lab.

## Quick Start

Run experiments with a fixed seed for reproducibility:

```bash
# Single scenario with seed
python run_experiment.py --scenario S1 --campaigns 100 --seed 42

# All scenarios with seed
python run_experiment.py --scenario all --campaigns 100 --seed 42

# Multi-detector comparison with seed
python run_experiment.py --scenario all --campaigns 100 --detector both --seed 42
```

## Random Seed Control

### Python Random Module

All experiments use both `random` and `numpy.random`:

```python
import random
import numpy as np

random.seed(42)
np.random.seed(42)
```

### Where Randomness Appears

1. **Campaign Generation**: Random selection of campaign family, beneficiaries, amounts
2. **Transaction Timing**: Random hour_of_day selection
3. **Attacker Behavior**: Random amount selection within ranges
4. **Environment State**: Initial account states, transaction routing

### Setting Seeds

**Via Command Line**:
```bash
python run_experiment.py --scenario all --seed 42
```

**Programmatically**:
```python
import random
import numpy as np

# Set both seeds
random.seed(42)
np.random.seed(42)

# Run experiment
from src.experiments.scenarios import ExperimentScenarios
scenarios = ExperimentScenarios(detector, environment)
results = scenarios.run_all_scenarios(100)
```

## Experiment Configuration

### Configuration Files

Save experiment parameters to ensure reproducibility:

```python
import json
from datetime import datetime

config = {
    'experiment_id': 'S1_reproduction_test',
    'timestamp': datetime.now().isoformat(),
    'random_seed': 42,
    'detector_model': 'baseline_xgboost.pkl',
    'campaign_type': 'known',
    'attacker_type': 'static',
    'num_campaigns': 100,
    'target_amount': 30000,
    'max_steps': 50,
    'accounts': 20
}

with open('results/configs/experiment_config.json', 'w') as f:
    json.dump(config, f, indent=2)
```

### Loading and Reproducing

```python
import json

# Load previous configuration
with open('results/configs/experiment_config.json') as f:
    config = json.load(f)

# Set seed
random.seed(config['random_seed'])
np.random.seed(config['random_seed'])

# Reproduce experiment with same parameters
detector = load_detector(f"models/{config['detector_model']}")
# ... run with same parameters
```

## Results Verification

### Checking Result Files

Results are saved with metadata for verification:

```bash
# View saved results
cat results/metrics/xgboost/S1_results.json
cat results/metrics/random_forest/S1_results.json
```

### Multi-Seed Validation

Test finding stability across seeds:

```bash
# Run with different seeds
for seed in 42 123 456 789 1000; do
    python run_experiment.py --scenario all --campaigns 50 --seed $seed
    mv results/metrics results/metrics_seed_${seed}
done

# Compare results
python compare_seed_results.py
```

## Multi-Detector Experiments

Run both detectors with same conditions:

```bash
# Both detectors, same seed
python run_experiment.py --scenario all --campaigns 100 --detector both --seed 42
```

Results saved to:
- `results/metrics/xgboost/` - XGBoost results
- `results/metrics/random_forest/` - Random Forest results

## Known Variability

### Expected Reproducibility

With **same seed**, these are reproducible:
- Campaign target amounts
- Campaign families selected
- Transaction amounts
- Transaction sequences
- Detector risk scores
- Final campaign status

### Expected Variability

Without seed control, these vary:
- Campaign success rates (stochastic behavior)
- Total financial exposure (depends on random transactions)
- Detection times (depends on transaction ordering)

### Seed-Dependent Findings

The S1 vs S2 difference is **seed-dependent**:
- Seed 42: Both ~100% success
- Other seeds: Static 96%, Adaptive 36%

This is **legitimate probabilistic behavior**, not a bug.

## Testing Reproducibility

### Unit Test

```bash
# Run reproducibility test
python -m pytest tests/test_core.py::TestReproducibility -v
```

### Manual Verification

```bash
# Run twice with same seed
python run_experiment.py --scenario S1 --campaigns 20 --seed 42 > run1.log
python run_experiment.py --scenario S1 --campaigns 20 --seed 42 > run2.log

# Compare outputs (should be identical)
diff run1.log run2.log
```

## Detector Reproducibility

### Model Files

Detector models are deterministic once trained:
- `models/baseline_xgboost.pkl` - XGBoost model (trained seed=42)
- `models/baseline_random_forest.pkl` - Random Forest model (trained seed=42)

### Retraining

To retrain detectors with same results:

```bash
# XGBoost
python train_upi_model.py  # Uses seed=42 internally

# Random Forest
python train_random_forest.py  # Uses seed=42 internally
```

## Campaign Family Reproducibility

Campaign families have fixed definitions:
- HIGH_VALUE_BURST: ₹10K-50K, high velocity
- SLOW_DRAIN: ₹1K-5K, low velocity
- GRADUAL_ESCALATION: ₹500-7K, progressive
- BENEFICIARY_HOPPING: ₹2K-4K, rotation

Within each family, specific amounts vary with seed.

## Environment State

### Initial Account Balances

Default: ₹100,000 per account

Set explicitly for reproducibility:
```python
environment = UPIEnvironment(fraud_detector=detector)
for account in accounts:
    environment.accounts[account] = 100000
```

### Transaction History

Environment maintains history during execution. For reproducibility:
1. Create new environment instance for each experiment
2. Use same seed
3. Use same account set

## Best Practices

### For Research Papers

1. Report exact seed used
2. Save full configuration to JSON
3. Document detector model versions
4. Report Python/numpy versions
5. Include result checksums

### For Development

1. Use fixed seed during debugging
2. Test with multiple seeds before finalizing
3. Document any seed-dependent behavior
4. Run full suite with seed=42 as baseline

### For Production

1. Use production-grade random sources
2. Don't rely on specific seed values
3. Test robustness across seed variations
4. Log actual seed used in each run

## Troubleshooting

### Results Don't Match

Check:
1. Same seed set for both `random` and `numpy.random`
2. Same detector model file
3. Same number of campaigns
4. Same account set
5. Same Python version

### Seed Doesn't Seem to Work

Verify seed is set **before** any random operations:
```python
# WRONG - random already used
generator = CampaignGenerator()
random.seed(42)

# RIGHT - seed first
random.seed(42)
np.random.seed(42)
generator = CampaignGenerator()
```

## Version Information

Record these for full reproducibility:
- Python version: 3.14.4 (or your version)
- NumPy version: Check with `pip show numpy`
- scikit-learn version: Check with `pip show scikit-learn`
- XGBoost version: Check with `pip show xgboost`

```bash
# Save environment
pip freeze > requirements_frozen.txt
```

## Summary

**Fully Reproducible** (with seed control):
✓ Campaign generation
✓ Transaction sequences
✓ Detector responses
✓ Final outcomes

**Probabilistically Varying** (without seed control):
✓ Success rate distributions
✓ Financial exposure totals
✓ Campaign-level randomness

**Always Deterministic**:
✓ Detector model predictions (given same features)
✓ Campaign family definitions
✓ Metric calculations

For questions or issues with reproducibility, refer to the test suite in `tests/test_core.py::TestReproducibility`.
