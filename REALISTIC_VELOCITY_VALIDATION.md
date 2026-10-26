> HISTORICAL SCOPE RECORD: The body below retains earlier claims and workspace paths, not current acceptance. Use the [current README](README.md), [verification report](docs/VERIFICATION_REPORT.md) and [handover](docs/HANDOVER.md) for present commands, counts and limitations. Historical completion/AUC/novelty/production claims are not adopted. Gate C remains HOLD.

# Realistic Velocity Validation Report

## Historical simulator validation

“Realistic” in the dated body is not evidence of real UPI traffic or production
robustness. Current feature-boundary tests and independently reconstructed
synthetic traces are described in `../FINAL_AUDIT_REPORT.md`.
Do not treat older metrics or counts below as this mission's results.
No external real-world validation is established; Gate C remains HOLD.

**Date**: 2026-09-18  
**Status**: ⚠️ PARTIAL IMPLEMENTATION - Timing Fixed, VPA Model Still Unrealistic  
**Version**: velocity_timing_v1

---

## Executive Summary

Implemented explicit transaction timing for campaigns to address the artificially low velocity issue identified in post-experiment analysis. Transaction timestamps now progress realistically based on campaign family timing models, and velocity is correctly computed from these timestamps.

**Key Finding**: While timing is now realistic, **campaign velocity remains much lower than training fraud** (0.05 vs 3.76 mean velocity) because campaigns use random VPA selection rather than modeling compromised accounts. The velocity mismatch is NOT due to timing artifacts - it's due to different fraud conceptual models.

### What Changed

✅ **Transaction timing**: Transactions now have explicit timestamps with realistic intervals  
✅ **Velocity calculation**: Correctly computed from transaction history and timestamps  
✅ **Family-specific timing**: Each campaign family has characteristic temporal behavior  
✅ **Reproducibility**: Timing is reproducible with seed control  

❌ **VPA modeling**: Still uses random selection, not compromised account model  
❌ **Campaign length**: Short campaigns (2-8 txns) don't accumulate velocity  
❌ **Velocity distribution**: Mean 0.05 vs training 3.76 (75x gap)  

### S1-S4 Results

Results remain similar to previous run: **100% campaign success**, low velocity throughout.

| Scenario | Success | Exposure | Mean Velocity (Campaign) | Mean Velocity (Training) |
|----------|---------|----------|--------------------------|--------------------------|
| **S1** | 100% | ₹45,326 | 0.00 | 3.76 |
| **S2** | 100% | ₹52,226 | 0.00 | 3.76 |
| **S3** | 100% | ₹16,661 | 0.10 | 3.76 |
| **S4** | 100% | ₹18,306 | 0.04 | 3.76 |

---

## A. What Changed

### 1. Campaign Timing Models

Created `src/campaigns/timing.py` with family-specific timing parameters:

| Family | Min Interval | Max Interval | Expected Velocity |
|--------|--------------|--------------|-------------------|
| **HIGH_VALUE_BURST** | 3 min | 15 min | 4-12 txns/hour |
| **SLOW_DRAIN** | 10 min | 30 min | 2-6 txns/hour |
| **GRADUAL_ESCALATION** | 5 min | 20 min | 3-9 txns/hour |
| **BENEFICIARY_HOPPING** | 4 min | 16.7 min | 3-10 txns/hour |

Each family now has characteristic inter-transaction intervals that produce realistic temporal patterns.

### 2. Attacker Timestamp Generation

Modified all attackers to generate timestamps:

```python
# Static, Adaptive, GradualEscalation, BeneficiaryHopping
self.timer = None  # Set by campaign executor

# In choose_action():
if self.timer:
    transaction["timestamp"] = self.timer.next_transaction_time()
```

### 3. Campaign Executor Integration

Updated `CampaignExecutor.execute_campaign()`:

```python
# Initialize timer based on campaign family
if campaign.family:
    timer = CampaignTimer(
        family=campaign.family,
        start_time=campaign.created_at,
        seed=seed
    )
    self.attacker.timer = timer
```

### 4. Environment Response

Modified `UPIEnvironment.process_transaction()` to return computed features:

```python
return {
    "transaction_id": transaction.transaction_id,
    "risk_score": risk_score,
    "decision": decision.value,
    "status": "success",
    "features": transaction.features  # Now included
}
```

### 5. Velocity Calculation (Already Correct)

Environment velocity calculation was already correct:

```python
def _compute_upi_features(self, transaction: Transaction) -> Dict:
    one_hour_ago = transaction.timestamp.timestamp() - 3600
    recent_from_vpa = [
        t for t in self.transactions
        if t.from_vpa == transaction.from_vpa
        and t.timestamp.timestamp() > one_hour_ago
    ]
    velocity_1h = len(recent_from_vpa)
```

No changes needed - already uses transaction timestamps correctly.

---

## B. Why Old Campaign Timing Was Unrealistic

### Problem 1: Implicit Same-Timestamp Transactions

**Before**: All transactions used `datetime.now()` at execution time
```python
# executor.py (old)
transaction['timestamp'] = datetime.now().isoformat()
```

**Result**: Transactions effectively occurred at the same instant (or within milliseconds), making velocity calculation impossible.

### Problem 2: No Family-Specific Temporal Behavior

**Before**: All campaigns had identical (implicit) timing  
**Result**: HIGH_VALUE_BURST and SLOW_DRAIN were indistinguishable in temporal dimension

### Problem 3: Non-Reproducible Timing

**Before**: Timestamps based on wall-clock time  
**Result**: Experiments were not reproducible - velocity would vary based on system load

---

## C. How Velocity Is Now Generated

### Velocity Emerges From Transaction History

1. **Timer initialized** with campaign family and seed
2. **Attacker calls** `timer.next_transaction_time()` for each transaction
3. **Timestamp added** to transaction before environment processing
4. **Environment computes** velocity from transaction history and current timestamp
5. **Velocity returned** in response features

### Example: HIGH_VALUE_BURST Campaign

```
Campaign: known_a68e4889 (HIGH_VALUE_BURST)

#   Timestamp    From VPA       Amount  Velocity  Risk    Decision
1   16:45:39     user6@upi      ₹19,515    0      0.1410  ALLOW
2   16:50:23     user6@upi      ₹31,348    1      0.2553  ALLOW
```

- **Transaction 1**: velocity=0 (no prior transactions from user6@upi)
- **Transaction 2**: velocity=1 (transaction 1 occurred 4m44s ago, within 1 hour)
- **Interval**: 284 seconds (realistic for HIGH_VALUE_BURST: 3-15 min range)

### Velocity Correctly Respects 1-Hour Window

Validated with controlled test:

```
Transaction 1 (T=0):      velocity=0 (no history)
Transaction 2 (T=30min):  velocity=1 (T1 counted)
Transaction 3 (T=65min):  velocity=1 (T1 outside window, only T2 counted)
```

✓ 1-hour window correctly enforced

---

## D. Validation of Velocity Calculation

### Test 1: Timing Model Validation

All four timing models produce realistic velocity ranges:

| Family | Avg Interval | Expected Velocity | Estimated Velocity |
|--------|--------------|-------------------|-------------------|
| HIGH_VALUE_BURST | 498s (8.3min) | 4-12 txns/hr | 7.2 txns/hr ✓ |
| SLOW_DRAIN | 1130s (18.8min) | 2-6 txns/hr | 3.2 txns/hr ✓ |
| GRADUAL_ESCALATION | 698s (11.6min) | 3-9 txns/hr | 5.2 txns/hr ✓ |
| BENEFICIARY_HOPPING | 576s (9.6min) | 3-10 txns/hr | 6.3 txns/hr ✓ |

### Test 2: Velocity From Timestamps

Campaign execution shows velocity correctly computed:

```
HIGH_VALUE_BURST campaign:
  Txn 1: from=user4@upi, time=16:43:52, velocity=0
  Txn 2: from=user2@upi, time=16:54:33, velocity=0  (different VPA)
  Txn 3: from=user4@upi, time=16:57:51, velocity=1  (user4 reused, T1 counted)
```

✓ Velocity increases when same VPA is reused within 1 hour

### Test 3: Fresh Environment Isolation

```
Campaign 1 velocities: [0, 0]
Campaign 2 velocities: [0]  (fresh environment)
```

✓ Fresh environments prevent velocity accumulation across campaigns

### Test 4: Reproducibility

**Issue**: Campaigns with same seed produce different transaction counts due to random VPA selection and target completion.

```
Run 1 velocities: [0]
Run 2 velocities: [0, 0]
```

**Interpretation**: Timing model IS reproducible (intervals are deterministic with seed), but campaign completion depends on random VPA selection, which affects when target is reached.

---

## E. New S1-S4 Results

### Campaign Success Rates (Unchanged)

| Scenario | Success Rate | Blocked | Detected | Total Exposure |
|----------|--------------|---------|----------|----------------|
| **S1** (Known + Static) | 100% | 0 | 5 | ₹2,266,316 |
| **S2** (Known + Adaptive) | 100% | 0 | 0 | ₹2,611,294 |
| **S3** (Unknown + Static) | 100% | 0 | 1 | ₹833,070 |
| **S4** (Unknown + Adaptive) | 100% | 0 | 0 | ₹915,292 |

### Campaign Velocity Distribution (NEW)

Measured from 20 sample campaigns (5 per scenario):

| Scenario | Mean Velocity | P90 Velocity | Max Velocity | Distribution |
|----------|---------------|--------------|--------------|--------------|
| **S1** | 0.00 | 0 | 0 | {0: 8} |
| **S2** | 0.00 | 0 | 0 | {0: 10} |
| **S3** | 0.10 | 1 | 1 | {0: 27, 1: 3} |
| **S4** | 0.04 | 0 | 1 | {0: 24, 1: 1} |

**Overall**: Mean velocity = 0.05, P90 = 0, Max = 1

### Risk Score Distribution (Representative Sample)

From campaign traces:

| Scenario | Min Risk | Max Risk | Typical Range |
|----------|----------|----------|---------------|
| HIGH_VALUE_BURST | 0.1351 | 0.2553 | 0.14-0.26 |
| SLOW_DRAIN | 0.0605 | 0.1058 | 0.06-0.11 |
| GRADUAL_ESCALATION | 0.0629 | 0.0828 | 0.06-0.08 |
| BENEFICIARY_HOPPING | 0.0657 | 0.0897 | 0.07-0.09 |

**All risk scores remain far below threshold** (0.92), even with realistic timing.

---

## F. Comparison With Previous Results

### What Changed

| Metric | Old Implementation | New Implementation | Change |
|--------|-------------------|-------------------|---------|
| **Transaction Timing** | Implicit (datetime.now()) | Explicit family-based intervals | ✓ Fixed |
| **Velocity Calculation** | From timestamps | From timestamps | No change (was correct) |
| **Velocity Distribution** | Mean ~0.6, P90 ~1 | Mean 0.05, P90 0 | **Worse** |
| **Campaign Success** | 100% S1-S4 | 100% S1-S4 | No change |
| **Risk Scores** | Max 0.22 | Max 0.26 | Slightly higher |
| **Threshold** | 0.92 | 0.92 | No change |

### What Did NOT Change

❌ **Campaign success rates**: Still 100% across all scenarios  
❌ **Detection rates**: Still near-zero  
❌ **Risk score range**: Still well below threshold  
❌ **Fundamental velocity problem**: Gap even larger

---

## G. What The Experiment Now Demonstrates

### Validated Claims

✅ **Transaction timing is now realistic**: Inter-transaction intervals match family models  
✅ **Velocity calculation works correctly**: Computed from timestamps, respects 1-hour window  
✅ **Fresh environments remain isolated**: No cross-campaign state accumulation  
✅ **Family-specific timing implemented**: Each family has characteristic temporal behavior  
✅ **Timing is reproducible**: Deterministic with seed control  

### Root Cause of Velocity Gap

The experiment now clearly demonstrates that **low campaign velocity is due to VPA modeling, not timing**:

1. **Random VPA Selection**: Attackers pick from 20 VPAs randomly for each transaction
   - Result: Most VPAs used only once → velocity = 0
   
2. **Short Campaign Duration**: Campaigns complete in 2-8 transactions (target reached)
   - Result: Not enough transactions from same source to accumulate velocity
   
3. **Conceptual Model Mismatch**: 
   - **Training fraud**: Aggregated historical patterns from compromised accounts (high velocity)
   - **Campaigns**: Individual attack episodes with tactical VPA diversity (low velocity)

### Example: S1 Campaign Breakdown

```
Campaign: known_a68e4889 (2 transactions, target ₹30,000)

Txn 1: user6@upi → user1@upi, ₹19,515, velocity=0
Txn 2: user6@upi → user0@upi, ₹31,348, velocity=1

Target reached (₹50,863 > ₹30,000), campaign SUCCESS
```

**Why velocity is low**: Only 2 transactions total, both from same source → max velocity = 1

**Why detector doesn't catch it**: velocity=1, amount moderate, hour daytime → risk 0.14-0.26 << threshold 0.92

---

## H. What Remains Unproven

### Cannot Conclude From Current Results

❌ **Whether detector can catch high-velocity campaigns**  
- Campaigns don't generate high velocity (mean 0.05 vs training 3.76)
- Never tested detector under realistic velocity conditions

❌ **Whether transaction-level features are sufficient**  
- Feature distribution mismatch (velocity dimension) invalidates test
- Would need velocity-matched campaigns to test this

❌ **Whether adaptive attackers can evade detector**  
- Both static and adaptive succeed at 100% due to low velocity
- Adaptation advantage not measurable

❌ **Whether detector performs differently on campaign patterns**  
- Campaigns are fundamentally different from training fraud (VPA model)
- Not testing same type of fraud

### What Next Experiment Should Test

To properly test "Can transaction-level detectors catch campaign-level fraud?":

**Option A: Compromised Account Model** (RECOMMENDED)
- Campaigns reuse the same source VPA for all transactions
- Simulates compromised account draining funds
- Generates realistic velocity (2-8 transactions from same source over 10-60 minutes)
- Expected outcome: Some campaigns detected due to high velocity

**Option B: Extended Campaign Duration**
- Increase target amounts to require 10-20 transactions
- Keep random VPA selection
- Longer campaigns accumulate more repeat-source transactions
- Expected outcome: Moderate velocity increase, some detection

**Option C: Historical Pattern Modeling**
- Campaigns represent aggregated historical fraud, not live episodes
- Pre-generate transaction history for source VPA
- Initialize environment with prior transactions
- Expected outcome: High velocity from start, significant detection

### Implementation Priority

1. **Option A** is most scientifically sound: models realistic fraud (compromised account)
2. **Option C** is most comparable to training: tests same fraud conceptual model
3. **Option B** is easiest change: minimal code modification

---

## I. Technical Implementation Details

### Files Modified

1. **src/campaigns/timing.py** (NEW)
   - `CampaignTimer`: Generates realistic timestamps
   - `TIMING_MODELS`: Family-specific timing parameters
   - Imports `CampaignFamily` from generator

2. **src/attackers/static.py**
   - Added `self.timer = None`
   - Updated transaction generation to include timestamps

3. **src/attackers/adaptive.py**
   - Added `self.timer = None`
   - Updated transaction generation to include timestamps

4. **src/attackers/family_based.py**
   - Updated `GradualEscalationAttacker` with timer
   - Updated `BeneficiaryHoppingAttacker` with timer

5. **src/campaigns/executor.py**
   - Initialize `CampaignTimer` based on campaign family
   - Pass timer to attacker
   - Remove timestamp override (was overwriting attacker timestamps)

6. **src/experiments/scenarios.py**
   - Pass `seed` parameter to all execute_campaign calls
   - Ensure reproducible timing across scenarios

7. **src/environment/simulator.py**
   - Store computed features in transaction object
   - Return features in process_transaction response
   - No changes to velocity calculation (was already correct)

### Validation Tests Created

1. **test_timing.py**
   - Timing model validation (intervals, velocity estimates)
   - Velocity from timestamps
   - 1-hour window enforcement
   - Fresh environment isolation
   - Reproducibility (partial - campaign length varies)
   - All family support

2. **trace_campaigns.py**
   - Representative traces for each family
   - Transaction-by-transaction details
   - Velocity progression visualization

3. **analyze_velocity.py**
   - Training vs campaign velocity comparison
   - Distribution analysis
   - Root cause diagnosis

### Test Results

**Passing**:
- ✓ Timing models produce realistic intervals
- ✓ Velocity computed from timestamps
- ✓ 1-hour window enforced
- ✓ Fresh environments isolated
- ✓ All families execute

**Issues**:
- ⚠️ Campaign velocity much lower than expected (0.05 vs 3.76)
- ⚠️ Reproducibility affected by random VPA selection

---

## J. Limitations of Current Implementation

### 1. VPA Model Does Not Match Training Fraud

**Training fraud assumption**: Sustained attack from compromised account
- Single source VPA used repeatedly
- Transactions accumulate over time
- High velocity emerges naturally

**Campaign model assumption**: Tactical attack with VPA diversity
- Random source VPA selection (anti-correlation strategy)
- Short-duration episodes
- Low velocity by design

**Impact**: Velocity distribution mismatch invalidates detector testing

### 2. Campaign Length Controlled By Target

Campaigns stop when target amount is reached (typically 2-8 transactions). This is realistic for goal-oriented fraud but prevents velocity accumulation.

**Trade-off**: 
- ✓ Realistic goal-oriented behavior
- ✗ Insufficient transactions for velocity

### 3. No Velocity Accumulation Across Attempts

Each campaign starts fresh - no prior transaction history. Real fraud might involve:
- Failed attempts before successful campaign
- Multiple campaigns from same compromised account
- Progressive velocity buildup

**Impact**: Campaigns never achieve training-like velocity patterns

### 4. Timing Is Realistic But VPA Selection Is Not

We fixed timing artifacts but revealed that VPA model is the real problem:
- Timing now realistic (validated)
- VPA selection remains unrealistic (random vs compromised-account model)

---

## K. Recommendations

### Immediate Next Step (HIGH PRIORITY)

**Implement compromised account model**:

```python
# In campaign executor
if campaign.family:
    # Use FIXED source VPA for all transactions
    source_vpa = f"compromised_{campaign.campaign_id}@upi"
    # Attacker reuses this VPA for all transactions
```

**Expected outcome**:
- Campaign velocity increases to 2-8 (realistic for campaign length)
- Some campaigns detected (high velocity + large amounts)
- Can finally test "do transaction features catch campaigns?"

### Alternative Approaches

**A. Extended Duration Campaigns**
- Increase target amounts (₹100K for known, ₹50K for unknown)
- More transactions → more chance of VPA reuse
- Velocity increases but still below training

**B. Pre-Seeded Transaction History**
- Initialize environment with prior transactions from source VPA
- Campaign starts with elevated velocity
- Tests detector under "ongoing attack" scenario

**C. Campaign Generator Redesign**
- Campaigns specify VPA reuse strategy
- HIGH_VALUE_BURST: fixed source VPA (compromised account)
- BENEFICIARY_HOPPING: rotate beneficiaries but fixed source
- SLOW_DRAIN: sustained attack from single source

### What NOT To Do

❌ **Do NOT lower detector threshold** to force detections  
❌ **Do NOT artificially inject velocity values** into features  
❌ **Do NOT claim detector fails** when we haven't tested it properly  
❌ **Do NOT add new models** before fixing VPA model  
❌ **Do NOT tune parameters** to create desired results  

---

## L. Scientific Integrity Statement

### What We Claimed To Fix

✓ "Implement realistic campaign velocity"

**Delivered**: Realistic transaction timing with family-specific intervals

### What We Actually Fixed

✓ Transaction timestamps now progress realistically  
✓ Velocity correctly computed from timestamps  
✓ 1-hour window properly enforced  
✓ Timing reproducible with seed  

### What We Did NOT Fix

❌ Campaign velocity distribution (mean 0.05 vs training 3.76)  
❌ VPA modeling (random selection vs compromised account)  
❌ Campaign length (too short to accumulate velocity)  
❌ Detector testing validity (feature mismatch persists)  

### Honest Assessment

**The velocity mismatch is NOT a timing bug - it's a fraud modeling problem.**

We implemented realistic transaction timing, but campaigns still don't generate high velocity because:
1. Random VPA selection prevents source reuse
2. Short campaigns (2-8 txns) can't accumulate velocity
3. Conceptual model differs from training (episode vs historical aggregation)

**Conclusion**: Timing implementation is correct and complete. Velocity gap requires VPA model redesign, not timing fixes.

---

## M. Summary Table

| Aspect | Old | New | Status |
|--------|-----|-----|--------|
| **Transaction Timing** | Implicit (datetime.now) | Explicit family-based | ✓ Fixed |
| **Velocity Calculation** | From timestamps | From timestamps | ✓ Already correct |
| **1-Hour Window** | Correct | Correct | ✓ Validated |
| **Fresh Environments** | Isolated | Isolated | ✓ Validated |
| **Reproducibility** | Wall-clock dependent | Seed-controlled timing | ✓ Fixed |
| **Velocity Distribution** | Mean ~0.6 | Mean 0.05 | ⚠️ Worse |
| **VPA Model** | Random selection | Random selection | ❌ Not addressed |
| **Campaign Success** | 100% | 100% | No change |
| **Detector Testing** | Invalid (low velocity) | Invalid (lower velocity) | ⚠️ Worse |

---

## N. Conclusion

**Timing implementation: SUCCESS**  
**Velocity distribution: FAILURE**  
**Overall: PARTIAL - Fixed wrong problem**

We successfully implemented realistic transaction timing and validated that velocity is correctly computed from timestamps. However, this revealed that **timing was never the root cause** of low campaign velocity.

The real issue is **VPA modeling**: campaigns use random VPA selection (anti-tracking strategy) rather than modeling compromised accounts (training fraud assumption). This fundamental mismatch means campaigns cannot generate high velocity even with perfect timing.

**Next step**: Implement compromised account model where campaigns reuse the same source VPA for all transactions, enabling realistic velocity accumulation and proper detector testing.

---

**Report Date**: 2026-09-18  
**Status**: ⚠️ PARTIAL IMPLEMENTATION  
**Next Action**: Implement compromised account model (Option A from recommendations)  
**Do NOT**: Lower thresholds, add new models, or claim detector failure before fixing VPA model
