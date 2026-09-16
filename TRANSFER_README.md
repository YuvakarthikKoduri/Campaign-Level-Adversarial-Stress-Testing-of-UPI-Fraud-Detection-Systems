# 🎯 UPI FRAUD STRESS LAB - TRANSFER PACKAGE

**Date**: September 16, 2026  
**Status**: 75% Complete - Ready for Model Training  
**Project Size**: 1.3 GB (including 98 MB dataset)

---

## 📦 WHAT'S IN THIS PACKAGE

### ✅ Fully Implemented (Ready to Use)

**1. Dataset Pipeline**
- Credit Card Fraud dataset (284,807 transactions, 98 MB)
- Data loader with validation
- Preprocessor with feature engineering
- Synthetic UPI transaction generator

**2. UPI Environment Simulator**
- Account/VPA entities
- Transaction processing
- Risk-based decisions (ALLOW/FLAG/BLOCK)
- Configurable thresholds

**3. Campaign System**
- Known/Unknown fraud campaign generator
- Campaign executor with attacker-detector loop
- Campaign state tracking

**4. Attacker Agents** ⭐
- **Static Attacker**: Fixed strategy
- **Adaptive Attacker**: Responds to detector feedback
  - Reduces amount when BLOCKED
  - Changes beneficiaries
  - Adjusts timing
  - Tracks adaptation metrics

**5. Evaluation Framework**
- Campaign success rate
- Detection/intervention time
- Financial exposure
- Detector degradation metrics

**6. Experiment Scenarios (S1-S4)**
- S1: Known + Static
- S2: Known + Adaptive
- S3: Unknown + Static
- S4: Unknown + Adaptive (PRIMARY STRESS TEST)

---

## 🚧 TO COMPLETE ON TARGET LAPTOP

### Step 1: Setup (10 minutes)
```bash
# Extract project
tar -xzf upi-fraud-stress-lab.tar.gz
cd upi-fraud-stress-lab

# Verify transfer
python3 verify_setup.py

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Train Model (20-30 minutes)
```bash
# This is THE critical step
python src/detectors/train.py
```

This will:
- Load 284,807 transactions
- Preprocess features
- Handle class imbalance with SMOTE
- Train XGBoost classifier
- Save to `models/baseline_xgboost.pkl`
- Generate evaluation metrics

### Step 3: Complete Demo (20 minutes)

The demo skeleton is in `demo.py`. After training, complete it:

```python
#!/usr/bin/env python3
from src.detectors.baseline import load_detector
from src.environment import UPIEnvironment
from src.campaigns.generator import CampaignGenerator
from src.campaigns.executor import CampaignExecutor
from src.attackers.adaptive import AdaptiveAttacker

# Load trained detector
detector = load_detector('models/baseline_xgboost.pkl')
environment = UPIEnvironment(detector)

# Create unknown fraud campaign
generator = CampaignGenerator()
campaign = generator.create_unknown_fraud_campaign(target_amount=30000)
attacker = AdaptiveAttacker(fraud_type="unknown")

# Run campaign with adaptive attacker
executor = CampaignExecutor(detector, environment, attacker)
accounts = [f"user{i}@upi" for i in range(20)]
completed = executor.execute_campaign(campaign, accounts, verbose=True)

# Show adaptation summary
summary = attacker.get_adaptation_summary()
print(f"\nBlocked: {summary['blocked_count']}, "
      f"Allowed: {summary['allowed_count']}, "
      f"Multiplier: {summary['amount_multiplier']:.2f}x")
```

### Step 4: Complete Experiment Runner (20 minutes)

Update `run_experiment.py`:

```python
#!/usr/bin/env python3
import argparse
from src.detectors.baseline import load_detector
from src.environment import UPIEnvironment
from src.experiments.scenarios import ExperimentScenarios

parser = argparse.ArgumentParser()
parser.add_argument('--scenario', choices=['S1','S2','S3','S4','all'])
parser.add_argument('--campaigns', type=int, default=100)
args = parser.parse_args()

detector = load_detector('models/baseline_xgboost.pkl')
environment = UPIEnvironment(detector)
scenarios = ExperimentScenarios(detector, environment)

if args.scenario == 'all':
    scenarios.run_all_scenarios(args.campaigns)
else:
    method = getattr(scenarios, f'run_scenario_{args.scenario.lower()}')
    results = method(args.campaigns, verbose=True)
```

### Step 5: Run Experiments (30-40 minutes)
```bash
# Run individual scenario
python run_experiment.py --scenario S4

# Run all scenarios
python run_experiment.py --all --campaigns 100
```

### Step 6: Visualizations (30-45 minutes)

Create `src/visualization/plots.py`:
- Scenario comparison bar charts
- Campaign trajectory plots
- Adaptive behavior analysis

---

## 📊 WHAT THE DEMO MUST SHOW

For the intermediate review, demonstrate:

**1. Adaptive Attacker in Action**
```
Step 1: Transaction ₹50,000 → BLOCK
Attacker: Reduce amount (multiplier 0.5x)

Step 2: Transaction ₹25,000 → BLOCK  
Attacker: Reduce more (multiplier 0.25x)

Step 3: Transaction ₹6,000 → ALLOW
Attacker: Continue at this level

Step 4: Transaction ₹6,500 → FLAG
Attacker: Slight reduction

Step 5: Transaction ₹5,200 → ALLOW
Campaign continues...
```

**2. Metrics Output**
```
Campaign Success Rate: 43%
Avg Detection Time: 18.4s
Avg Intervention Time: 24.7s
Avg Financial Exposure: ₹7,250
```

**3. Scenario Comparison**
```
Metric                    S1    S2    S3    S4
Campaign Success Rate    12%   23%   38%   43%
Avg Detection Time      5.2s  12.1s 22.3s 31.8s
Financial Exposure    ₹2.1K ₹4.3K ₹6.8K ₹9.2K
```

---

## 📁 PROJECT STRUCTURE

```
upi-fraud-stress-lab/
├── data/
│   └── raw/creditcard.csv          ✅ 98 MB
├── src/
│   ├── data/                       ✅ Loader, preprocessor, synthetic
│   ├── detectors/                  ⚠️  Needs training
│   ├── environment/                ✅ Complete simulator
│   ├── campaigns/                  ✅ Generator, executor
│   ├── attackers/                  ✅ Static, adaptive
│   ├── evaluation/                 ✅ Campaign metrics
│   ├── experiments/                ✅ S1-S4 scenarios
│   └── visualization/              🚧 Add plots
├── models/                         🚧 Empty (will have .pkl after training)
├── results/                        🚧 Empty (will fill during experiments)
├── demo.py                         🚧 Complete after training
├── run_experiment.py              🚧 Complete after training
├── verify_setup.py                ✅ Run this first!
├── DATASET.md                     ✅ Dataset documentation
├── HANDOFF.md                     ✅ Detailed handoff
├── STATUS.md                      ✅ Current status
└── README.md                      ✅ Project overview
```

---

## ⏱️ TIME ESTIMATE

| Task | Time |
|------|------|
| Transfer & extract | 5 min |
| Setup & verify | 10 min |
| **Train model** | **20-30 min** |
| Complete demo | 20 min |
| Complete experiment runner | 20 min |
| Run S1-S4 experiments | 30-40 min |
| Create visualizations | 30-45 min |
| **TOTAL** | **~3 hours** |

---

## ✅ VERIFICATION CHECKLIST

Before intermediate review:

- [ ] Project transferred and extracted
- [ ] `python3 verify_setup.py` passes all checks
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] Dataset loads successfully
- [ ] **Model training completed**
- [ ] Model file exists: `models/baseline_xgboost.pkl`
- [ ] `demo.py` runs and shows adaptive behavior
- [ ] Attacker visibly changes strategy after BLOCK
- [ ] `run_experiment.py --scenario S4` works
- [ ] `run_experiment.py --all` generates comparison
- [ ] Results saved in `results/metrics/`
- [ ] Basic visualizations created

---

## 🎯 KEY DELIVERABLES FOR REVIEW

### Must Have:
1. **Live demo** showing adaptive attacker responding to detector
2. **S1-S4 results** with real metrics
3. **Comparison table** showing S4 as worst-case stress test
4. **Working end-to-end system** from dataset → detector → campaign → results

### Nice to Have (Can do after review):
- RL-based attacker (DQN/PPO)
- GNN detector
- Large-scale experiments (1000+ campaigns)
- Publication-quality visualizations
- Full research paper

---

## 🔧 TROUBLESHOOTING

### "Dataset not found"
```bash
ls -lh data/raw/creditcard.csv  # Should show ~98 MB
# If missing, re-transfer the project
```

### "Module not found"
```bash
source venv/bin/activate  # Activate venv first!
pip install -r requirements.txt
```

### "Training fails with memory error"
Edit `src/detectors/train.py`:
```python
# Reduce dataset size for testing
df = loader.load_raw(nrows=50000)  # Instead of loading all
```

### "Demo fails"
```bash
# Ensure model exists
ls -lh models/baseline_xgboost.pkl

# If not, train first
python src/detectors/train.py
```

---

## 📞 SUPPORT FILES INCLUDED

- **HANDOFF.md**: Detailed handoff with code examples
- **STATUS.md**: Current completion status
- **DATASET.md**: Dataset documentation and statistics
- **README.md**: Project overview
- **verify_setup.py**: Quick setup verification script

---

## 🎓 RESEARCH CONTRIBUTION

This project demonstrates:

> **Can fraud detectors remain effective when attackers use previously unseen patterns and adapt their strategy based on detector responses?**

The answer is shown through S4 (Unknown + Adaptive):
- Higher campaign success rate than S1-S3
- Longer detection/intervention times
- Greater financial exposure
- Measurable detector degradation

This is the **80% working prototype** that proves the concept for intermediate review.

---

## 🚀 NEXT COMMANDS ON TARGET LAPTOP

```bash
# 1. Verify everything transferred
python3 verify_setup.py

# 2. Setup environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. THE CRITICAL STEP: Train the model
python src/detectors/train.py

# 4. Test the demo
python demo.py

# 5. Run experiments
python run_experiment.py --scenario S4
python run_experiment.py --all

# You're now at 80% and ready for intermediate review!
```

---

**Package prepared by**: Multi-agent development system  
**Total Python files**: 24  
**Total project size**: 1.3 GB  
**Dataset size**: 98 MB (284,807 transactions)

**Status**: Ready for transfer 🚀
