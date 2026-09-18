# UPI Fraud Stress Lab - Research Findings

**Date**: 2026-09-18  
**Investigation**: Scientific analysis of experimental results  
**Status**: CRITICAL ISSUES FOUND - Results require reinterpretation

---

## Executive Summary

Investigation revealed that the reported experimental results contain a **critical environmental artifact** that invalidates the primary finding. The 0% success rate for S4 (Unknown + Adaptive) is NOT evidence of detector robustness, but rather a consequence of **velocity accumulation** in the shared environment across sequential campaigns.

---

## Critical Finding: Environmental Velocity Accumulation

### The Problem

The `UPIEnvironment` maintains a shared `self.transactions` list that accumulates across all campaigns run in the same environment instance. The velocity feature is calculated as:

```python
# From src/environment/simulator.py, line 191-198
one_hour_ago = transaction.timestamp.timestamp() - 3600
recent_from_vpa = [
    t for t in self.transactions
    if t.from_vpa == transaction.from_vpa
    and t.timestamp.timestamp() > one_hour_ago
]
velocity_1h = len(recent_from_vpa)
```

Since experiments run 30 campaigns sequentially in the **same environment instance**, the transaction history grows with each campaign. Later campaigns have higher velocity values even though they use different VPAs.

### Evidence

**Test 1: S4 Success Rate vs Campaign Count (seed=42, XGBoost)**

| Campaigns | Successes | Success Rate | Avg Exposure |
|-----------|-----------|--------------|--------------|
| 5         | 5         | 100.0%       | ₹17,916      |
| 10        | 10        | 100.0%       | ₹18,151      |
| 15        | 14        | 93.3%        | ₹16,887      |
| 20        | 18        | 90.0%        | ₹16,906      |
| 25        | 20        | 80.0%        | ₹14,912      |
| 30        | 20        | 66.7%        | ₹12,738      |

**Conclusion**: Success rate **decreases systematically** as more campaigns are run, not because later campaigns are harder, but because velocity accumulates.

**Test 2: Isolated Campaign Execution**

When running S4 campaigns with fresh environments each time (not shared):
- All campaigns succeed (100% in small-scale tests)
- Risk scores remain low (0.001-0.01 range)
- No velocity accumulation

### Impact

This invalidates the following claims:
1. ❌ "S4 achieves 0% success, demonstrating detector robustness"
2. ❌ "Adaptive attackers fail on unknown fraud patterns"
3. ❌ "The detector effectively catches unknown adaptive attacks"

The actual finding is:
✓ **Environmental state accumulation creates an unintended experiment artifact that blocks later campaigns**

---

## Current Experimental Results (seed=42, 30 campaigns, XGBoost)

### S1: Known + Static
- **Success Rate**: 100.0% (30/30)
- **Total Exposure**: ₹1,351,720
- **Avg Exposure**: ₹45,057
- **Interpretation**: Known fraud patterns with static behavior succeed completely

### S2: Known + Adaptive  
- **Success Rate**: 96.7% (29/30)
- **Total Exposure**: ₹1,437,369
- **Avg Exposure**: ₹47,912
- **Interpretation**: Adaptive behavior on known patterns also succeeds, slightly lower than static (1 campaign blocked)

### S3: Unknown + Static
- **Success Rate**: 13.3% (4/30)
- **Total Exposure**: ₹148,704
- **Avg Exposure**: ₹4,957
- **Interpretation**: Unknown fraud patterns with static behavior are largely blocked (26/30 campaigns blocked)

### S4: Unknown + Adaptive
- **Success Rate**: 0.0% in 30-campaign run, but 100.0% in 5-campaign run
- **Total Exposure**: ₹2,743 (30 campaigns), ₹89,579 (5 campaigns)
- **Avg Exposure**: ₹91 (30 campaigns), ₹17,916 (5 campaigns)
- **Interpretation**: Result is **environmentally dependent**, not a valid detector robustness measure

---

## Investigation 1: Static vs Adaptive Comparison (Same Campaign)

**Setup**: Run S3 and S4 with identical seed (42) to compare static vs adaptive on the SAME campaign family

**Campaign Family**: beneficiary_hopping (both)

**Results**:

| Attacker | Amount Moved | Transactions | Success | Avg Amount per Txn |
|----------|--------------|--------------|---------|-------------------|
| Static   | ₹16,741      | 8            | ✓       | ₹2,093           |
| Adaptive | ₹17,734      | 5            | ✓       | ₹3,547           |

**Transaction Comparison**:

| Step | Static Amount | Adaptive Amount | Static Risk | Adaptive Risk |
|------|---------------|-----------------|-------------|---------------|
| 1    | ₹1,445        | ₹2,767          | 0.0014      | 0.0025        |
| 2    | ₹1,893        | ₹3,456          | 0.0014      | 0.0011        |
| 3    | ₹1,348        | ₹3,290          | 0.0014      | 0.0011        |
| 4    | ₹1,119        | ₹4,074          | 0.0012      | 0.0016        |
| 5    | ₹3,021        | ₹4,147          | 0.0011      | 0.0009        |
| 6    | ₹1,795        | -               | 0.0014      | -             |
| 7    | ₹1,882        | -               | 0.0014      | -             |
| 8    | ₹4,238        | -               | 0.0018      | -             |

**Findings**:
1. **Adaptive succeeds faster**: 5 transactions vs 8 transactions
2. **Adaptive uses larger amounts**: Avg ₹3,547 vs ₹2,093
3. **Both succeed**: No blocking occurred (in isolated test)
4. **Risk scores remain low**: All below 0.003 (very safe)

**Conclusion**: When tested in **isolation** (not sequential with other campaigns), both static and adaptive attackers succeed on unknown fraud patterns.

---

## Investigation 2: Campaign Family Analysis

Analyzed 5 campaigns from each family with static attackers:

### HIGH_VALUE_BURST (Known)
- **Amount Range**: ₹11,266 - ₹49,776
- **Mean Amount**: ₹32,164
- **Risk Score Mean**: 0.0065
- **Allow Rate**: 100.0%
- **Classification**: KNOWN (matches training distribution)

### SLOW_DRAIN (Unknown)
- **Amount Range**: ₹1,115 - ₹4,978
- **Mean Amount**: ₹2,949
- **Risk Score Mean**: 0.0055
- **Allow Rate**: 100.0%
- **Classification**: UNSEEN (smaller amounts than training)

### GRADUAL_ESCALATION (Unknown)
- **Amount Range**: ₹1,115 - ₹4,971
- **Mean Amount**: ₹3,022
- **Risk Score Mean**: 0.0621
- **Allow Rate**: 93.3%
- **Classification**: UNSEEN (progressive pattern not in training)

### BENEFICIARY_HOPPING (Unknown)
- **Amount Range**: ₹1,553 - ₹4,946
- **Mean Amount**: ₹3,053
- **Risk Score Mean**: 0.1218
- **Allow Rate**: 80.0%
- **Classification**: UNSEEN (rotation pattern not in training)

**Key Observations**:
1. **HIGH_VALUE_BURST has lowest risk** despite highest amounts - this is expected as it matches training
2. **BENEFICIARY_HOPPING has highest risk** (0.1218) - detector is somewhat sensitive to this pattern
3. **All families allow most transactions** when tested in isolation
4. **Unknown families are not inherently undetectable** - they're just different mechanisms

---

## Investigation 3: Why S1 Achieves 100% Success

Tested 5 S1 campaigns (Known + Static, seed=200-204):

**All 5 campaigns succeeded**:
- Campaign 1: ₹32,758 moved (target ₹30,000), 2 txns, avg risk 0.0033
- Campaign 2: ₹62,939 moved (target ₹30,000), 3 txns, avg risk 0.0053
- Campaign 3: ₹40,555 moved (target ₹30,000), 1 txn, avg risk 0.0066
- Campaign 4: ₹59,255 moved (target ₹30,000), 3 txns, avg risk 0.0050
- Campaign 5: ₹44,254 moved (target ₹30,000), 2 txns, avg risk 0.0025

**Why S1 Succeeds**:
1. **High transaction amounts** (₹11K-₹50K per transaction) → reach target in 1-3 transactions
2. **Risk scores remain very low** (avg 0.003-0.007) → well below FLAG threshold
3. **Amounts match training distribution** → detector sees them as legitimate-like
4. **Quick completion** → minimal opportunity for accumulation effects

**Is this realistic?**
- YES: High-value fraud that matches training patterns IS hard to detect
- NO indication that S1 is "too easy" - this is the expected baseline

---

## Metric Naming Issue

### test_families.py Success Rates

The script reports success rates like 162.8%, 106.2%, etc.

**Formula**: `(amount_moved / target_amount) * 100`

**Example**: 
- Target: ₹30,000
- Moved: ₹48,850
- "Success rate": 162.8%

**Issue**: This is **NOT** a success rate, it's **attainment percentage** or **target overshoot**.

**Recommendation**: 
- Rename metric to `target_attainment_pct` or `amount_moved_pct`
- Keep campaign success rate as binary: did campaign reach target (yes/no)?

---

## Correct Interpretation of Results

### What We Can Validly Conclude

1. **Known fraud with high amounts succeeds easily** (S1: 100%)
   - Detector has blind spots for training-like patterns
   - High transaction amounts allow quick target attainment

2. **Adaptive behavior on known fraud is nearly as effective** (S2: 96.7%)
   - 1 campaign blocked out of 30
   - Adaptation does not significantly hurt performance on known patterns

3. **Unknown fraud patterns ARE partially detected** (S3: 13.3%)
   - 26/30 campaigns blocked with static attacker
   - Detector shows some generalization beyond training

4. **Environmental artifacts invalidate S4 conclusions**
   - Cannot conclude detector robustness from current S4 results
   - Velocity accumulation confounds the measurement

### What We CANNOT Validly Conclude

1. ❌ "Adaptive attackers always fail on unknown patterns"
2. ❌ "S4 demonstrates detector robustness against adaptive attacks"
3. ❌ "0% success in S4 proves the system works"
4. ❌ "Unknown fraud is undetectable"

---

## Root Causes

### Environmental Design Issue

**Problem**: `ExperimentScenarios` reuses the same `UPIEnvironment` instance across all campaigns

```python
# From src/experiments/scenarios.py
def run_scenario_s4(self, num_campaigns: int = 100, ...):
    campaigns = []
    for i in range(num_campaigns):
        campaign = self.campaign_generator.create_unknown_fraud_campaign()
        attacker = AdaptiveAttacker(fraud_type="unknown")
        executor = CampaignExecutor(self.detector, self.environment, attacker)  # SHARED environment
        completed_campaign = executor.execute_campaign(campaign, accounts, ...)
        campaigns.append(completed_campaign)
```

**Consequence**: `self.environment.transactions` list grows with each campaign, causing velocity feature to increase artificially for later campaigns.

**Why it matters**: Velocity is a strong fraud signal in the training data. Higher velocity → higher risk scores → more blocks.

---

## Recommended Fixes

### Fix 1: Isolate Campaign Environments (Recommended)

**Option A**: Create fresh environment for each campaign
```python
for i in range(num_campaigns):
    campaign = self.campaign_generator.create_unknown_fraud_campaign()
    attacker = AdaptiveAttacker(fraud_type="unknown")
    fresh_environment = UPIEnvironment(fraud_detector=self.detector)  # NEW
    executor = CampaignExecutor(self.detector, fresh_environment, attacker)
    ...
```

**Pro**: Each campaign evaluated independently  
**Con**: Loses cross-campaign transaction history (may be desired for realistic environment)

**Option B**: Clear transaction history between campaigns
```python
for i in range(num_campaigns):
    self.environment.transactions.clear()  # Reset
    campaign = self.campaign_generator.create_unknown_fraud_campaign()
    ...
```

**Pro**: Simple fix  
**Con**: Still shares VPA registration state

### Fix 2: Use Different VPA Namespaces

Ensure each campaign uses unique VPAs so velocity doesn't accumulate:
```python
def _generate_test_accounts(self, campaign_id: int, num_accounts: int = 20):
    return [f"camp{campaign_id}_user{i}@upi" for i in range(num_accounts)]
```

### Fix 3: Timestamp Campaigns Realistically

Add time gaps between campaigns so they're outside the 1-hour velocity window:
```python
import time
for i in range(num_campaigns):
    time.sleep(3601)  # Wait 1 hour + 1 second
    ...
```

**Pro**: Most realistic  
**Con**: Experiments take days to run

---

## Next Experiments (After Fixes)

### Experiment 1: Multi-Seed Validation

Run 10-30 seeds for each scenario to get distributional statistics:
- Mean, median, std dev of success rates
- Confidence intervals
- Statistical significance testing (S1 vs S2, S3 vs S4)

### Experiment 2: Isolated Campaign Evaluation

Test individual campaigns with fresh environments:
- Does the detector actually catch unknown patterns in isolation?
- What features drive detection?
- Are there genuine blind spots?

### Experiment 3: Feature Attribution Analysis

For blocked vs allowed transactions:
- Which features contribute most to risk score?
- Do unknown patterns trigger specific feature combinations?
- Can we identify what makes a pattern "unseen"?

### Experiment 4: Threshold Sensitivity

Vary detector thresholds to understand:
- At what threshold does S3 go from 13% to 0%?
- Are current thresholds appropriate?
- Trade-off between false positives and campaign success

---

## Limitations of Current System

### Detector Limitations

1. **Feature set is minimal**: Only 4 features (amount, hour, velocity, is_new_vpa)
2. **No sequence modeling**: Detector sees individual transactions, not campaign patterns
3. **No beneficiary tracking**: Rotation patterns (BENEFICIARY_HOPPING) not directly modeled
4. **Training data limitations**: Synthetic data may not capture real fraud complexity

### Experimental Limitations

1. **Small campaign counts**: 30 campaigns insufficient for statistical conclusions
2. **Environmental confounds**: Velocity accumulation invalidates sequential results
3. **Single detector comparison**: Only XGBoost and Random Forest tested
4. **Synthetic campaigns**: Real attackers may behave differently

### Attacker Limitations

1. **Adaptive attacker is naive**: Only tracks safe amounts/beneficiaries, no sophisticated strategy
2. **No meta-learning**: Attacker doesn't learn detector's decision boundary
3. **No evasion techniques**: No timing manipulation, amount obfuscation, etc.

---

## Honest Assessment

### What This System Successfully Demonstrates

1. ✓ Campaign-level evaluation framework is operational
2. ✓ Multiple campaign families with distinct behaviors exist
3. ✓ Static vs adaptive comparison methodology is sound (when not confounded)
4. ✓ Detector has measurable blind spots on known fraud patterns
5. ✓ Framework is extensible for future experiments

### What Remains Unproven

1. ? Whether adaptive attackers meaningfully outperform static on unknown patterns
2. ? Whether the detector has genuine robustness against adversarial adaptation
3. ? Whether unknown campaign families are actually "unseen" by the detector's feature space
4. ? Statistical significance of observed differences

### Critical Next Step

**Fix the environmental velocity accumulation before drawing any conclusions about S4 results.**

The current S4 finding (0% success) is an **artifact**, not a research contribution.

---

## Conclusion

The UPI Fraud Stress Lab successfully implements a campaign-level adversarial evaluation framework, but the current experimental results contain a critical environmental artifact that invalidates the primary finding about S4 (Unknown + Adaptive) scenarios.

The 0% success rate in S4 is NOT evidence of detector robustness, but rather a consequence of velocity accumulation in the shared environment instance across sequential campaigns. When tested in isolation, S4 campaigns succeed at 100%.

**Immediate action required**: Fix environmental isolation before conducting further experiments or drawing conclusions about detector robustness against adaptive attacks.

---

**Report Date**: 2026-09-18  
**Status**: Research findings documented, critical issue identified  
**Recommendation**: Fix environmental artifact, rerun experiments with proper isolation, conduct multi-seed validation

