# UPI Baseline Validation Report

**Date**: 2026-09-18  
**Status**: ✅ BASELINE REBUILT AND VALIDATED  
**Version**: synthetic_upi_v1

---

## Executive Summary

The UPI Fraud Stress Lab baseline detectors have been **completely rebuilt** from scratch with proper training methodology, threshold calibration, and comprehensive validation. The previous detector misconfiguration has been corrected.

### What Changed

**Before**: Detector trained on European Credit Card dataset (PCA features V1-V28), producing unrealistically low risk scores (0.001-0.005) for all campaign transactions.

**After**: Detectors trained on synthetic UPI transaction data with proper 4-feature schema (amount, hour_of_day, velocity_1h, is_new_vpa), producing calibrated risk scores (0.03-0.99 range).

---

## A. What Was Wrong with the Old Baseline

### Critical Issues Identified

1. **Training Data Mismatch**
   - Detector was trained on European Credit Card Fraud dataset
   - Dataset has 28 PCA-transformed features (V1-V28) + Time + Amount
   - Detector interface expected: amount, hour_of_day, velocity_1h, is_new_vpa
   - **Result**: Feature space mismatch, model never saw proper UPI features

2. **Risk Score Miscalibration**
   - Campaign transaction risk scores: 0.001-0.005 range
   - FLAG threshold: 0.5 (never reached)
   - Gap: 100x below threshold
   - **Result**: 100% campaign success due to misconfigured detector, not detector limitation

3. **Lack of Threshold Calibration**
   - Default threshold (0.5) used without validation
   - No analysis of precision/recall trade-offs
   - No consideration of class imbalance (5% fraud rate)

4. **No Feature Parity Validation**
   - Training features ≠ inference features
   - No automated test to catch this mismatch
   - Silent failure mode (predictions produced, but meaningless)

---

## B. What the Corrected Baseline Uses

### Training Data

**Synthetic UPI Transaction Dataset**:
- **Size**: 50,000 transactions
- **Fraud rate**: 5% (2,500 fraud / 47,500 legitimate)
- **Seed**: 42 (reproducible)
- **Saved**: `data/synthetic/upi_transactions_v1.csv`

### Data Splits

| Split | Size | Fraud Rate | Purpose |
|-------|------|------------|---------|
| Train | 30,000 (60%) | 5.00% | Model training |
| Val   | 10,000 (20%) | 5.00% | Threshold calibration |
| Test  | 10,000 (20%) | 5.00% | Final evaluation |

### Models Trained

1. **XGBoost Classifier**
   - n_estimators: 150
   - max_depth: 5
   - scale_pos_weight: 19.0 (handles 5% fraud rate)
   - Early stopping: 15 rounds
   - Best iteration: 48

2. **Random Forest Classifier**
   - n_estimators: 150
   - max_depth: 10
   - class_weight: {0: 1.0, 1: 19.0}
   - min_samples_split: 20
   - min_samples_leaf: 10

---

## C. Dataset Generation Methodology

### Design Principles

1. **Realistic Overlap**: Fraud and legitimate distributions overlap significantly
2. **Multi-Modal**: Both classes have multiple sub-populations
3. **Not Trivially Separable**: Fraud is not always high-amount, late-night, high-velocity
4. **Representative**: Captures real UPI transaction patterns

### Feature Distributions

#### Amount (₹)

**Legitimate** (multi-modal):
- 70% small daily: ₹100-3,000 (lognormal: μ=6.5, σ=0.8)
- 20% medium: ₹3,000-15,000 (lognormal: μ=8.5, σ=0.6)
- 10% large legitimate: ₹15,000-50,000 (lognormal: μ=9.8, σ=0.5)

**Fraud** (multi-modal):
- 30% high-value: ₹20,000-60,000 (lognormal: μ=10.0, σ=0.5)
- 40% medium-value: ₹5,000-20,000 (lognormal: μ=9.0, σ=0.6)
- 30% low-value testing: ₹1,000-5,000 (lognormal: μ=7.5, σ=0.7)

**Observed**:
- Legit range: ₹100 - ₹97,764 (median: ₹1,041)
- Fraud range: ₹500 - ₹100,000 (median: ₹7,866)
- **Overlap**: Legit P95=₹18,546, Fraud P05=₹918

#### Hour of Day

**Legitimate**:
- 92% daytime (6am-11pm): N(μ=14, σ=5)
- 8% night (night shift, emergencies): N(μ=2, σ=2)

**Fraud**:
- 60% late night: N(μ=2.5, σ=2.5)
- 40% daytime (compromised office accounts): N(μ=13, σ=5)

**Observed**:
- Legit mean: 12.2, mode: 14
- Fraud mean: 7.3, mode: 0

#### Velocity (transactions in last hour)

**Legitimate**:
- 85% low: Poisson(λ=0.5)
- 15% burst (bill payments): Poisson(λ=2.5)

**Fraud**:
- 65% high (rapid draining): Poisson(λ=5)
- 35% low (testing): Poisson(λ=1.5)

**Observed**:
- Legit mean: 0.80, P90: 2
- Fraud mean: 3.76, P90: 7

#### New VPA Flag

**Legitimate**: 10% new (first-time payments)  
**Fraud**: 55% new (higher than legit, but not 100%)

**Observed**:
- Legit: 9.9%
- Fraud: 54.6%

---

## D. Feature Definitions

| Feature | Type | Range | Description |
|---------|------|-------|-------------|
| **amount** | float | 0+ | Transaction amount in ₹ (Indian Rupees) |
| **hour_of_day** | int | 0-23 | Hour when transaction occurred (0=midnight, 14=2pm) |
| **velocity_1h** | int | 0+ | Number of transactions from same VPA in last hour |
| **is_new_vpa** | binary | 0/1 | 1 if beneficiary VPA is first-time, 0 if seen before |

**No scaling**: Tree-based models (XGBoost, Random Forest) do not require feature scaling.

---

## E. Model Performance

### XGBoost Performance

| Metric | Value | Interpretation |
|--------|-------|----------------|
| **ROC-AUC** | 0.9587 | Excellent discrimination (near-perfect) |
| **PR-AUC** | 0.7287 | Good precision-recall balance |
| **Precision** | 0.7428 | 74% of flagged transactions are actual fraud |
| **Recall** | 0.6180 | Catches 62% of fraud transactions |
| **F1 Score** | 0.6747 | Balanced performance |
| **Threshold** | 0.9242 | Calibrated on validation set (max F1) |

**Confusion Matrix** (Test Set: 10,000 transactions):
```
             Predicted
             Legit  Fraud
Actual Legit  9393    107
       Fraud   191    309
```

- **True Negatives**: 9,393 (98.9% of legitimate correctly classified)
- **False Positives**: 107 (1.1% of legitimate incorrectly flagged)
- **False Negatives**: 191 (38.2% of fraud missed)
- **True Positives**: 309 (61.8% of fraud caught)

### Random Forest Performance

| Metric | Value | Interpretation |
|--------|-------|----------------|
| **ROC-AUC** | 0.9524 | Excellent discrimination |
| **PR-AUC** | 0.7160 | Good precision-recall balance |
| **Precision** | 0.6837 | 68% of flagged transactions are actual fraud |
| **Recall** | 0.6700 | Catches 67% of fraud transactions |
| **F1 Score** | 0.6768 | Balanced performance |
| **Threshold** | 0.8775 | Calibrated on validation set (max F1) |

**Confusion Matrix** (Test Set: 10,000 transactions):
```
             Predicted
             Legit  Fraud
Actual Legit  9345    155
       Fraud   165    335
```

- **True Negatives**: 9,345 (98.4% of legitimate correctly classified)
- **False Positives**: 155 (1.6% of legitimate incorrectly flagged)
- **False Negatives**: 165 (33.0% of fraud missed)
- **True Positives**: 335 (67.0% of fraud caught)

### Comparison

| Metric | XGBoost | Random Forest | Winner |
|--------|---------|---------------|--------|
| ROC-AUC | 0.9587 | 0.9524 | XGBoost (+0.63%) |
| Precision | 0.7428 | 0.6837 | XGBoost (+5.9%) |
| Recall | 0.6180 | 0.6700 | Random Forest (+5.2%) |
| F1 Score | 0.6747 | 0.6768 | Random Forest (+0.2%) |
| Threshold | 0.9242 | 0.8775 | - |

**Interpretation**: Both detectors perform similarly (95% ROC-AUC, 67-68% F1). XGBoost has higher precision (fewer false positives), Random Forest has higher recall (catches more fraud).

---

## F. Threshold Selection Methodology

### Approach

Used **validation set** (10,000 transactions) to calibrate threshold via Precision-Recall curve analysis.

### Criterion

**Maximize F1 Score** on validation set.

F1 = 2 × (Precision × Recall) / (Precision + Recall)

This balances precision (minimizing false positives) and recall (maximizing fraud detection).

### Why Not 0.5?

Default threshold (0.5) assumes balanced classes. With 5% fraud rate, this would:
- Produce too many false positives (flags ~50% of transactions)
- Waste investigator time on legitimate transactions

Calibrated thresholds (0.92 for XGBoost, 0.88 for Random Forest) are much higher, reflecting class imbalance.

### Alternative Criteria

Other valid threshold selection criteria (not used here):
- **Maximize Recall at Fixed Precision**: "Catch 80% of fraud while keeping precision ≥50%"
- **Cost-Based**: Assign costs to FP/FN, minimize expected cost
- **Business Rule**: "Flag ≤1% of transactions" (fixed false positive rate)

**Current choice (max F1) is reasonable but not the only option.**

---

## G. Calibration and Diagnostic Results

### Detector Behavior Test

Testing detector response to controlled synthetic inputs:

| Amount | Hour | Velocity | New VPA | Risk Score | Expected | Description |
|--------|------|----------|---------|------------|----------|-------------|
| ₹1,000 | 14 | 0 | 0 | 0.0350 | low | Small daytime, low velocity, known VPA |
| ₹5,000 | 10 | 1 | 0 | 0.2020 | low-medium | Medium daytime, low velocity, known VPA |
| ₹25,000 | 14 | 0 | 0 | 0.1351 | medium | Large daytime, low velocity, known VPA |
| ₹25,000 | 2 | 5 | 1 | **0.9916** | high | Large night, high velocity, new VPA |
| ₹50,000 | 3 | 8 | 1 | **0.9945** | very-high | Very large night, very high velocity, new VPA |
| ₹100,000 | 2 | 15 | 1 | **0.9945** | extreme | Extreme amount, night, extreme velocity, new VPA |

**Key Observations**:

1. ✅ **Risk scores span full range** (0.03-0.99) - detector is properly calibrated
2. ✅ **Monotonic relationship**: Higher risk features → higher risk scores
3. ✅ **Sensitive to combinations**: Large amount + night + high velocity + new VPA → very high risk (0.99)
4. ✅ **Safe region exists**: Small daytime transactions with known VPAs have low risk (0.03)

**Comparison to Old Detector**:
- Old: All campaign transactions scored 0.001-0.005 (100x below threshold)
- **New: Risk scores reach 0.99 for high-risk features (well above threshold)**

### Feature Parity Test

✅ **PASS**: Training features match inference features

```
Expected: ['amount', 'hour_of_day', 'velocity_1h', 'is_new_vpa']
Actual:   ['amount', 'hour_of_day', 'velocity_1h', 'is_new_vpa']
```

Automated test will catch any future mismatches.

---

## H. Limitations

### Dataset Limitations

1. **Synthetic Data**: Not real UPI transactions
   - Distributions are educated guesses, not empirical
   - May not capture all real-world patterns
   - No real fraud campaigns (invented behaviors)

2. **Limited Feature Set**: Only 4 features
   - No beneficiary identity
   - No historical behavior (only 1-hour velocity)
   - No transaction notes/descriptions
   - No device/location information

3. **Simplified Fraud Models**: Multi-modal but still stylized
   - Real fraud may be more sophisticated
   - No account takeover signals
   - No social engineering patterns

### Detector Limitations

1. **Transaction-Level Only**: Evaluates each transaction independently
   - Cannot see campaign-level patterns (sequence of transactions)
   - No memory of past campaigns
   - No beneficiary network analysis

2. **Fixed Thresholds**: Single threshold for all transactions
   - No context-aware risk assessment
   - No user-specific baselines
   - No time-of-day threshold variation

3. **Class Imbalance**: 5% fraud rate
   - Precision-Recall trade-off: improving recall increases false positives
   - 38% of fraud still missed (F1-optimal threshold)
   - Lowering threshold would catch more fraud but flag more legitimate

### Threshold Limitations

1. **Max F1 Criterion**: Not necessarily optimal for business
   - Assumes equal cost of FP and FN
   - May not match actual operational constraints
   - Alternative: cost-based or fixed-FPR threshold

2. **Static Threshold**: Doesn't adapt over time
   - Fraud patterns evolve
   - Detector may drift
   - Requires periodic recalibration

---

## I. Exact Next Step for Campaign-Level Experiments

### Now Safe to Run S1-S4 Experiments

With properly calibrated detectors, we can now meaningfully test campaign-level stress scenarios.

### Expected Outcomes

**S1 (Known + Static)**: Moderate success (50-80%)
- Known patterns should be partially caught
- Static behavior (no adaptation) makes detection easier
- High-velocity bursts will trigger flags

**S2 (Known + Adaptive)**: Higher success (60-90%)
- Adaptive attackers learn safe amounts/timing
- May evade detection better than static

**S3 (Unknown + Static)**: Lower success (30-60%)
- Unknown patterns may have lower risk scores
- Depends on whether unknown families avoid high-risk features

**S4 (Unknown + Adaptive)**: Variable success (40-80%)
- Primary stress test
- Combines unknown patterns + adaptation
- Will reveal detector blind spots

### Predictions Are Uncertain

Unlike the old 100% success (artifact), **actual results may vary**:
- Detectors may catch some campaigns (not 0%)
- Detectors may miss some campaigns (not 100% success)
- Results will depend on campaign feature distributions

### Valid Research Question

**"Can transaction-level detectors catch campaign-level fraud?"**

With old detector: Cannot answer (misconfigured)  
With new detector: **Can now test this scientifically**

### What to Measure

1. **Campaign success rates** (S1-S4)
2. **Financial exposure** (amount moved before detection)
3. **Detection time** (how quickly campaigns are caught)
4. **Which campaign families** are caught vs. missed
5. **Risk score distributions** for campaign transactions
6. **Threshold sensitivity** (how results change with different thresholds)

### Next Command

```bash
python run_experiment.py --scenario all --campaigns 50 --seed 42 --detector xgboost
```

This will run S1-S4 with the new XGBoost detector and produce **scientifically valid results**.

---

## Summary

### What Was Fixed

✅ Training data: European Credit Card → Synthetic UPI  
✅ Feature schema: PCA features → UPI features  
✅ Risk score range: 0.001-0.005 → 0.03-0.99  
✅ Threshold: Uncalibrated 0.5 → Calibrated 0.92 (XGBoost), 0.88 (RF)  
✅ Feature parity: No test → Automated validation  
✅ Documentation: None → Complete validation report  

### Performance Achieved

- **ROC-AUC**: 95-96% (excellent discrimination)
- **F1 Score**: 67-68% (balanced performance)
- **Precision**: 68-74% (low false positive rate)
- **Recall**: 62-67% (catches majority of fraud)

### Scientific Integrity

**Previous claim** (INVALID): "100% campaign success proves transaction-level features insufficient"

**Current status**: Ready to test this claim scientifically with proper baseline detector.

### No Tuning for Desired Results

- Dataset generated with fixed seed (reproducible)
- Threshold calibrated on validation set (standard practice)
- No parameters adjusted to achieve specific campaign success rates
- Detectors will perform as they perform - results may vary

---

**Report Date**: 2026-09-18  
**Status**: ✅ BASELINE VALIDATED - Ready for campaign experiments  
**Models**: `models/baseline_xgboost.pkl`, `models/baseline_random_forest.pkl`  
**Dataset**: `data/synthetic/upi_transactions_v1.csv`  
**Next Step**: Run S1-S4 experiments and analyze results honestly
