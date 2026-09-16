# UPI Fraud Stress Lab - Handoff Document

**Status**: Ready for Model Training on Target Laptop

---

## Current Status: 75% Complete

### ✅ Completed Components

1. **Project Infrastructure (M0)**
   - Directory structure
   - Python project files (pyproject.toml, requirements.txt)
   - Git repository initialized
   - Virtual environment created

2. **Dataset (M1)**
   - Credit Card Fraud dataset downloaded (102 MB)
   - Data loader implemented (`src/data/loader.py`)
   - Data preprocessor implemented (`src/data/preprocessor.py`)
   - Synthetic UPI generator implemented (`src/data/synthetic.py`)

3. **UPI Environment (M3)**
   - Account/VPA entities (`src/environment/entities.py`)
   - UPI simulator (`src/environment/simulator.py`)
   - Risk thresholds (`src/environment/thresholds.py`)

4. **Campaign System (M4)**
   - Campaign generator (`src/campaigns/generator.py`)
   - Campaign executor with attacker-detector loop (`src/campaigns/executor.py`)

5. **Attacker Agents (M5)**
   - Static attacker (`src/attackers/static.py`)
   - Adaptive attacker (`src/attackers/adaptive.py`)

6. **Evaluation System**
   - Campaign-level metrics (`src/evaluation/metrics.py`)
   - Experiment scenarios S1-S4 (`src/experiments/scenarios.py`)

7. **Detector Infrastructure (M2 - Partial)**
   - Detector class with clean interface (`src/detectors/baseline.py`)
   - Training script ready (`src/detectors/train.py`)
   - **WAITING**: Model training to be done on target laptop

---

## 🚧 Remaining Work (25%)

### Critical Path (Target Laptop)

**Step 1: Train the Baseline Detector**

```bash
# On target laptop:
cd upi-fraud-stress-lab
source venv/bin/activate

# Train the model
python src/detectors/train.py

# This will:
# - Load and preprocess data
# - Train XGBoost classifier
# - Save model to models/baseline_xgboost.pkl
# - Generate evaluation metrics
```

**Step 2: Complete Integration (M6)**

After training, integrate all components:

```python
# Test the full pipeline
from src.detectors.baseline import load_detector
from src.environment import UPIEnvironment
from src.campaigns.generator import CampaignGenerator
from src.campaigns.executor import CampaignExecutor
from src.attackers.adaptive import AdaptiveAttacker

# Load trained detector
detector = load_detector('models/baseline_xgboost.pkl')

# Create environment
environment = UPIEnvironment(detector)

# Run a test campaign
campaign = CampaignGenerator().create_unknown_fraud_campaign()
attacker = AdaptiveAttacker(fraud_type="unknown")
executor = CampaignExecutor(detector, environment, attacker)

accounts = [f"user{i}@upi" for i in range(20)]
completed_campaign = executor.execute_campaign(campaign, accounts, verbose=True)

print(f"Campaign status: {completed_campaign.status.value}")
print(f"Amount moved: ₹{completed_campaign.total_amount_moved:,.2f}")
```

**Step 3: Build Demo Script**

Update `demo.py` to show live demonstration:

```python
# See section below for complete demo implementation
```

**Step 4: Build Experiment Runner**

Update `run_experiment.py` to run S1-S4 scenarios:

```python
# See section below for complete experiment runner
```

**Step 5: Add Visualizations (M8)**

Create visualization scripts in `src/visualization/`:
- Scenario comparison bar charts
- Campaign trajectory plots
- Adaptive behavior analysis

---

## File Transfer Instructions

### Required Files for Target Laptop

**Transfer the entire project directory:**

```bash
# Create archive (on current laptop)
cd /home/yuvakarthik-koduri
tar -czf upi-fraud-stress-lab.tar.gz upi-fraud-stress-lab/

# Transfer to target laptop (use USB, network, etc.)

# Extract on target laptop
tar -xzf upi-fraud-stress-lab.tar.gz
cd upi-fraud-stress-lab
```

**Critical files present:**
- ✅ Dataset: `data/raw/creditcard.csv` (102 MB)
- ✅ All source code in `src/`
- ✅ Virtual environment setup scripts
- ✅ Requirements file

---

## Setup on Target Laptop

```bash
# 1. Navigate to project
cd upi-fraud-stress-lab

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Verify dataset
python -c "
import pandas as pd
df = pd.read_csv('data/raw/creditcard.csv', nrows=100)
print(f'Dataset loaded: {len(df)} rows')
print(f'Fraud column present: {\"Class\" in df.columns}')
"

# 5. Train the model
python src/detectors/train.py

# 6. Verify model was created
ls -lh models/baseline_xgboost.pkl

# 7. Test the demo
python demo.py

# 8. Run experiments
python run_experiment.py --scenario S4
```

---

## Complete Demo Implementation

Create this in `demo.py`:

```python
#!/usr/bin/env python3
"""Live demonstration of adaptive attacker."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.detectors.baseline import load_detector
from src.environment import UPIEnvironment
from src.campaigns.generator import CampaignGenerator
from src.campaigns.executor import CampaignExecutor
from src.attackers.adaptive import AdaptiveAttacker

def main():
    print("="*60)
    print("UPI FRAUD STRESS LAB - LIVE DEMO")
    print("="*60)
    print()
    
    # Load detector
    print("Loading trained detector...")
    detector = load_detector('models/baseline_xgboost.pkl')
    
    # Create environment
    environment = UPIEnvironment(detector)
    
    # Create unknown fraud campaign
    generator = CampaignGenerator()
    campaign = generator.create_unknown_fraud_campaign(target_amount=30000)
    
    # Create adaptive attacker
    attacker = AdaptiveAttacker(fraud_type="unknown")
    
    # Execute campaign
    executor = CampaignExecutor(detector, environment, attacker)
    accounts = [f"user{i}@upi" for i in range(20)]
    
    print("Executing campaign with adaptive attacker...")
    print()
    
    completed = executor.execute_campaign(campaign, accounts, verbose=True)
    
    # Show adaptation summary
    if hasattr(attacker, 'get_adaptation_summary'):
        summary = attacker.get_adaptation_summary()
        print("\nAdaptive Behavior Summary:")
        print(f"  Total steps: {summary['steps']}")
        print(f"  Blocked: {summary['blocked_count']}")
        print(f"  Flagged: {summary['flagged_count']}")
        print(f"  Allowed: {summary['allowed_count']}")
        print(f"  Final amount multiplier: {summary['amount_multiplier']:.2f}x")
        print(f"  Unique beneficiaries used: {summary['unique_beneficiaries']}")

if __name__ == "__main__":
    main()
```

---

## Complete Experiment Runner

Update `run_experiment.py`:

```python
#!/usr/bin/env python3
"""Experiment runner for S1-S4 scenarios."""

import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.detectors.baseline import load_detector
from src.environment import UPIEnvironment
from src.experiments.scenarios import ExperimentScenarios

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scenario', choices=['S1', 'S2', 'S3', 'S4', 'all'])
    parser.add_argument('--campaigns', type=int, default=100)
    args = parser.parse_args()
    
    # Load detector
    detector = load_detector('models/baseline_xgboost.pkl')
    environment = UPIEnvironment(detector)
    
    scenarios = ExperimentScenarios(detector, environment)
    
    if args.scenario == 'all':
        results = scenarios.run_all_scenarios(args.campaigns)
    else:
        method = getattr(scenarios, f'run_scenario_{args.scenario.lower()}')
        results = method(args.campaigns, verbose=True)
        print(f"\n{args.scenario} Results:")
        for k, v in results.items():
            print(f"  {k}: {v}")

if __name__ == "__main__":
    main()
```

---

## Expected Timeline on Target Laptop

1. **Setup & Install** (5-10 minutes)
2. **Model Training** (10-30 minutes depending on hardware)
3. **Integration Testing** (10-15 minutes)
4. **Demo Implementation** (15-20 minutes)
5. **Experiment Runner** (10-15 minutes)
6. **Run S1-S4** (20-40 minutes)
7. **Visualizations** (30-45 minutes)

**Total: 2-3 hours to reach 80% working prototype**

---

## Verification Checklist

After setup on target laptop, verify:

- [ ] Virtual environment activated
- [ ] All dependencies installed
- [ ] Dataset loads successfully
- [ ] Model training completes
- [ ] Model file created (models/baseline_xgboost.pkl)
- [ ] Demo runs and shows adaptive behavior
- [ ] Experiment runner works for S1-S4
- [ ] Results saved to results/metrics/

---

## Architecture Diagram

```
Dataset (creditcard.csv)
        ↓
Preprocessor → Features
        ↓
XGBoost Detector ← [TRAIN ON TARGET LAPTOP]
        ↓
UPI Environment
        ↓
Campaign Generator
        ↓
Campaign Executor
        ↓
Static Attacker / Adaptive Attacker
        ↓
Detector Response
        ↓
Attacker Observes & Adapts
        ↓
Campaign Result
        ↓
Metrics & Evaluation
        ↓
Visualization
```

---

## Contact Points for Issues

### If Dataset Won't Load
- Verify: `data/raw/creditcard.csv` exists (102 MB)
- Check: File has "Class" column for fraud labels
- Solution: Re-download from Kaggle if corrupted

### If Training Fails
- Check: pandas, scikit-learn, xgboost installed
- Check: Sufficient RAM (recommend 4GB+)
- Solution: Reduce dataset size in `train.py` (use nrows parameter)

### If Demo Fails
- Check: Model file exists at `models/baseline_xgboost.pkl`
- Check: All imports work
- Solution: Run training first

---

## Next Steps After 80% Prototype

These can be completed **after** the intermediate review:

1. **RL-based Attacker**
   - DQN implementation
   - PPO implementation
   - Compare with rule-based

2. **Advanced Detector**
   - GNN-based detector
   - Ensemble methods

3. **Large-Scale Experiments**
   - 1000+ campaigns per scenario
   - Statistical significance testing

4. **Publication-Quality Visualizations**
   - Professional plots
   - LaTeX integration

5. **Research Paper**
   - Full methodology
   - Literature review
   - Results analysis

---

## File Manifest

```
upi-fraud-stress-lab/
├── data/
│   └── raw/creditcard.csv          ✅ 102 MB
├── src/
│   ├── data/
│   │   ├── loader.py               ✅ Complete
│   │   ├── preprocessor.py         ✅ Complete
│   │   └── synthetic.py            ✅ Complete
│   ├── detectors/
│   │   ├── baseline.py             ✅ Complete
│   │   └── train.py                ✅ Ready
│   ├── environment/
│   │   ├── entities.py             ✅ Complete
│   │   ├── simulator.py            ✅ Complete
│   │   └── thresholds.py           ✅ Complete
│   ├── campaigns/
│   │   ├── generator.py            ✅ Complete
│   │   └── executor.py             ✅ Complete
│   ├── attackers/
│   │   ├── static.py               ✅ Complete
│   │   └── adaptive.py             ✅ Complete
│   ├── evaluation/
│   │   └── metrics.py              ✅ Complete
│   └── experiments/
│       └── scenarios.py            ✅ Complete
├── demo.py                         🚧 Needs completion
├── run_experiment.py               🚧 Needs completion
└── requirements.txt                ✅ Complete
```

---

**Project handoff complete. Ready for model training on target laptop.**
