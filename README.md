# UPI Fraud Stress Lab

**Campaign-Level Adversarial Stress Testing of UPI Fraud Detection Systems**

## Overview

This project evaluates the resilience of fraud detection systems under UPI-specific campaign-level scenarios involving previously unseen and strategically adaptive fraud behavior.

## Status: 80% Working Prototype (Intermediate Review)

Current implementation includes:
- ✅ Baseline fraud detector (XGBoost)
- ✅ UPI-like transaction environment
- ✅ Campaign simulator (known/unknown fraud)
- ✅ Static and adaptive attackers
- ✅ Four experimental scenarios (S1-S4)
- ✅ Campaign-level metrics
- ✅ Live demonstration
- 🚧 RL-based attacker (future work)

## Quick Start

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run demo
python demo.py

# Run experiments
python run_experiment.py --scenario S4
python run_experiment.py --all
```

## Architecture

```
Dataset → Detector → Environment → Campaign → Attacker → Adaptation → Metrics
```

## Core Research Question

> Can an existing fraud detector remain effective when an attacker uses previously unseen fraud behavior and changes its strategy based on the detector's responses?

## Project Structure

```
upi-fraud-stress-lab/
├── data/               # Datasets
├── models/             # Trained models
├── src/                # Source code
│   ├── data/           # Data processing
│   ├── detectors/      # Fraud detectors
│   ├── environment/    # UPI simulator
│   ├── campaigns/      # Campaign generator
│   ├── attackers/      # Attacker agents
│   ├── experiments/    # Experiment runner
│   └── visualization/  # Metrics & plots
├── results/            # Experiment results
└── demo.py             # Live demonstration
```

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [METHODOLOGY.md](METHODOLOGY.md) - Research methodology
- [DATASET.md](DATASET.md) - Dataset documentation
- [EXPERIMENTS.md](EXPERIMENTS.md) - Experiment protocols

## License

Research prototype - not for production use.
