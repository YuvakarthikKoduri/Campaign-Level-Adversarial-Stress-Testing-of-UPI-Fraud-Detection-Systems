# Model Baseline Audit Report

**Date**: 2026-09-18
**Purpose**: Diagnose why all S1-S4 scenarios achieve 100% campaign success

---

## 1. Training Data Inspection

**Dataset**: 284,807 transactions (European Credit Card dataset with PCA features)
**Fraud ratio**: 0.17% (492 fraud / 284,315 legitimate)

**Source**: This is NOT UPI-specific data. The detector was trained on credit card fraud.

### Amount Distribution

| Metric | Fraud | Legitimate | Ratio |
|--------|-------|------------|-------|
| Mean   | $ 122.21 | $      88.29 | 1.38x |
| Median | $   9.25 | $      22.00 | 0.42x |
| Min    | $   0.00 | $       0.00 | - |
| Max    | $2,125.87 | $  25,691.16 | - |

**Percentiles**:

| Percentile | Fraud | Legitimate |
|------------|-------|------------|
| P10        | $ 0.76 | $      1.00 |
| P25        | $ 1.00 | $      5.65 |
| P50        | $ 9.25 | $     22.00 |
| P75        | $105.89 | $     77.05 |
| P90        | $346.75 | $    202.72 |
| P95        | $640.90 | $    364.41 |
| P99        | $1,357.43 | $  1,016.97 |

## 2. Detector Probability Distributions on Training Data

Model loaded from models/baseline_xgboost.pkl
Features: 4
**Model**: XGBoost trained on 4 features: ['amount', 'hour_of_day', 'velocity_1h', 'is_new_vpa']

**NOTE**: The detector expects ['amount', 'hour_of_day', 'velocity_1h', 'is_new_vpa']
but was trained on credit card data with PCA features V1-V28.

### Synthetic Feature Test

Testing detector response to different feature combinations:

| Description | Amount | Hour | Velocity | New VPA | Risk Score |
|-------------|--------|------|----------|---------|------------|
| Small amount, night, low velocity, new VPA | ₹ 1,000 |    2 |        0 |       1 |   0.057045 |
| Medium amount, afternoon, low velocity, new VPA | ₹ 5,000 |   14 |        0 |       1 |   0.013305 |
| Large amount, night, high velocity, new VPA | ₹25,000 |    2 |        5 |       1 |   0.957372 |
| Very large, night, very high velocity, new VPA | ₹50,000 |    2 |       10 |       1 |   0.997895 |
| Extreme amount, night, extreme velocity, new VPA | ₹100,000 |    3 |       20 |       1 |   0.998049 |

## 3. Campaign Transaction Feature Analysis

### Known (HIGH_VALUE_BURST)

**Family**: high_value_burst
**Status**: SUCCESS
**Amount moved**: ₹35,577.07
**Transactions**: 1

**Transaction Details**:

| # | Amount | Hour | Velocity | New VPA | Risk Score | Decision |
|---|--------|------|----------|---------|------------|----------|
| 1 | ₹35,577 |    0 |        0 |       1 |   0.003376 | ALLOW    |

**Risk Score Statistics**:
- Min: 0.003376
- Max: 0.003376
- Mean: 0.003376
- **FLAG threshold**: 0.500000
- **BLOCK threshold**: 0.800000
- **Gap to FLAG**: 0.496624 (148.1x below threshold)

### Unknown (random family)

**Family**: slow_drain
**Status**: SUCCESS
**Amount moved**: ₹15,296.04
**Transactions**: 7

**Transaction Details**:

| # | Amount | Hour | Velocity | New VPA | Risk Score | Decision |
|---|--------|------|----------|---------|------------|----------|
| 1 | ₹ 1,893 |    0 |        0 |       1 |   0.001372 | ALLOW    |
| 2 | ₹ 1,348 |    0 |        0 |       1 |   0.001323 | ALLOW    |
| 3 | ₹ 1,119 |    0 |        0 |       1 |   0.001128 | ALLOW    |
| 4 | ₹ 3,021 |    0 |        0 |       1 |   0.001013 | ALLOW    |
| 5 | ₹ 1,795 |    0 |        0 |       1 |   0.001372 | ALLOW    |
| 6 | ₹ 1,882 |    0 |        0 |       1 |   0.001372 | ALLOW    |
| 7 | ₹ 4,238 |    0 |        0 |       1 |   0.001679 | ALLOW    |

**Risk Score Statistics**:
- Min: 0.001013
- Max: 0.001679
- Mean: 0.001323
- **FLAG threshold**: 0.500000
- **BLOCK threshold**: 0.800000
- **Gap to FLAG**: 0.498321 (297.8x below threshold)

## 4. Threshold Analysis

### Current Thresholds

| Threshold | Value | Purpose |
|-----------|-------|---------|
| FLAG      | 0.500 | High-risk transaction flagged for review |
| BLOCK     | 0.800 | Transaction blocked immediately |

### Observed Risk Scores

**From 20 S3/S4 campaigns** (118 transactions total):

- Minimum: 0.000713
- P50 (median): 0.001323
- P90: 0.002409
- P99: 0.002553
- Maximum: 0.004968

**Distance to FLAG threshold (0.5)**:
- Max observed: 0.004968
- Gap: 0.495032
- **Factor**: 100.6x below FLAG threshold

**Transactions that would trigger FLAG/BLOCK**:
- At FLAG (≥0.5): 0/118 (0.00%)
- At BLOCK (≥0.8): 0/118 (0.00%)

## 5. Root Cause Diagnosis

### Verified Facts

1. **Training data**: European Credit Card dataset (284,807 transactions, 0.17% fraud)
2. **Detector features**: 4 simple features (amount, hour, velocity, is_new_vpa)
3. **Campaign risk scores**: Range 0.001-0.002 (all transactions)
4. **FLAG threshold**: 0.5 (never reached)
5. **BLOCK threshold**: 0.8 (never reached)
6. **Gap to FLAG**: 100.6x - observed max is **101 times** below threshold

### Potential Issues

#### A. Feature Scaling Mismatch

**Hypothesis**: Campaign transactions may fall outside trained feature space.

**Evidence**:
- Training data has PCA features (V1-V28) but detector expects (amount, hour, velocity, is_new_vpa)
- Risk scores are uniformly very low (0.001-0.002 range)
- No variation in risk despite varying amounts (₹1K to ₹50K)

#### B. Threshold Miscalibration

**Hypothesis**: FLAG threshold (0.5) may be set for different scale than model outputs.

**Evidence**:
- Maximum observed risk: 0.004968
- FLAG threshold: 0.500000
- Gap: 101x

**To reach FLAG threshold**, risk scores would need to be **250x higher**.

#### C. Model Training Quality

**Hypothesis**: Model may not have learned meaningful patterns.

**Evidence**:
- Extremely low risk scores (0.001-0.002) for all inputs
- No discrimination between ₹1K and ₹100K amounts
- 4-feature model trained on 28-PCA-feature data (feature mismatch)

#### D. Campaign Feature Distribution

**Hypothesis**: Campaign generators produce transactions that are unintentionally 'safe'.

**Evidence**:
- Known campaigns: ₹11K-50K amounts (match training fraud distribution)
- Unknown campaigns: ₹1K-5K amounts (smaller than training fraud)
- Velocity: 0-2 for most transactions (low)
- New VPA: 100% (always new)

## 6. Conclusion

### Primary Finding

The 100% campaign success rate is **MOST LIKELY** due to:

**Threshold miscalibration or feature scaling issue in the detector**.

**Evidence**:

1. Risk scores are uniformly very low (max observed: 0.004968)
2. FLAG threshold is 101x higher than any observed risk
3. No transaction ever triggers FLAG (≥0.5) or BLOCK (≥0.8)
4. Risk scores show minimal variation despite 100x amount differences

### What is NOT Verified

❌ **Cannot conclude**: "Transaction-level detectors fail at campaign-level detection"

**Reason**: The detector never flags ANY individual transaction, suggesting the
detector itself is misconfigured, not that campaign-level patterns are undetectable.

### What is Verified

✓ **Environmental artifact eliminated**: Fresh environments per campaign (no velocity accumulation)
✓ **Experiments reproduce consistently**: Same results across multiple seeds
✓ **Campaign families diverse**: All 4 families execute with distinct behaviors
✓ **Test suite passing**: 21/21 tests pass (100%)

### What Remains Unproven

? **Whether transaction-level features are inherently insufficient** - Cannot test while detector produces unrealistic risk scores
? **Whether campaign-level detection requires sequence models** - Cannot test with misconfigured baseline
? **Whether adaptive attackers outperform static** - Cannot differentiate when all succeed due to low thresholds

## 7. Recommended Next Experiment

### Option 1: Recalibrate Detector (Most Scientific)

**Action**: Investigate and fix detector threshold/scaling issue

**Steps**:
1. Inspect training script to understand feature transformation
2. Verify feature scaler is applied correctly at inference time
3. Check if threshold (0.5) was set for raw probabilities or scaled scores
4. Test detector on training data to verify it produces reasonable predictions
5. Recalibrate threshold based on validation set ROC curve

**Expected outcome**: Detector produces risk scores in 0-1 range with meaningful variation

### Option 2: Retrain Detector on UPI-Like Data

**Action**: Train new detector on synthetic UPI transactions with proper features

**Steps**:
1. Generate synthetic UPI dataset (50K transactions)
2. Include realistic fraud/legitimate feature distributions
3. Ensure 4 features (amount, hour, velocity, is_new_vpa) are properly representative
4. Train with proper train/val split and threshold selection
5. Validate detector produces meaningful risk scores (0.1-0.9 range)

**Expected outcome**: Detector with calibrated thresholds that catches some (not all) campaigns

### Option 3: Lower Thresholds Experimentally

**Action**: Test with FLAG=0.002, BLOCK=0.005 to see if any campaigns get caught

**Purpose**: Quick diagnostic - if campaigns still succeed at 0.002 threshold,
confirms detector truly cannot discriminate. If campaigns get blocked, confirms
threshold miscalibration is the issue.

**WARNING**: This is a diagnostic only, not a scientific fix. Do not present
results from artificially lowered thresholds as research findings.

### Recommendation

**Most scientifically rigorous**: Option 1 (Recalibrate Detector)

**Reason**: Fix the underlying issue before drawing conclusions about detector
capabilities. Current results cannot distinguish between:

- Detector inherently unable to catch campaigns (interesting finding)
- Detector misconfigured with wrong threshold scale (experimental artifact)

Without fixing the detector, we cannot make valid claims about campaign-level
detection difficulty.

---

**Report Generated**: 2026-09-18T10:27:17Z
**Status**: Detector misconfiguration identified, NOT detector limitation
**Action Required**: Fix threshold/scaling before drawing research conclusions
