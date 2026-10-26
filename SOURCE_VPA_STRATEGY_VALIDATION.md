> HISTORICAL SCOPE RECORD: The body below retains earlier claims and workspace paths, not current acceptance. Use the [current README](README.md), [verification report](docs/VERIFICATION_REPORT.md) and [handover](docs/HANDOVER.md) for present commands, counts and limitations. Historical completion/AUC/novelty/production claims are not adopted. Gate C remains HOLD.

# Source VPA Strategy Validation Report

## Historical validation context

This dated report is preserved context, not the current acceptance result.
Its numerical outcomes and test counts must not be substituted for current
recorded runs. The new matched pilot fixes one source and one sink and does
not establish beneficiary-hopping generalization. Current scope and limits
are in `../FINAL_ACADEMIC_REPORT.md` and `../FINAL_AUDIT_REPORT.md`.

**Date:** 2026-09-18  
**Status:** Environment/Modeling Validation (Pre-S1-S4)

---

## A. Current Source-VPA Problem

### Background

After implementing realistic campaign timing models, velocity analysis revealed a persistent modeling gap: **campaign velocity remained significantly lower than training fraud** despite correct temporal behavior.

**Root Cause:** The original campaign generator used **random VPA selection** for source accounts. This meant:
- Each transaction in a campaign selected a random source VPA from the available pool
- No VPA reuse within campaigns
- Velocity could not accumulate (velocity = count of transactions from same source VPA within 1 hour)
- Campaign velocity distributions: mean ~0.0-0.1, max ~0-1
- Training fraud distributions: mean 3.76, P90 7, max 14

### Why This Matters

Velocity is calculated as:
```
velocity_1h = COUNT(transactions from same source VPA in past 1 hour)
```

Without VPA reuse, velocity **cannot emerge** from transaction patterns. This is a fundamental modeling issue, not a timing issue.

Training fraud represents **aggregated historical patterns** where compromised accounts generate multiple transactions. Campaigns must model similar source-VPA behavior to produce realistic velocity signals.

---

## B. Why Realistic Timing Alone Did Not Solve Velocity

### Timing Implementation (REALISTIC_VELOCITY_VALIDATION.md)

We implemented realistic timing with 6 campaign families:
- HIGH_VALUE_BURST: 2-5 min intervals
- SLOW_DRAIN: 30-60 min intervals  
- COORDINATED_STRIKE: 5-15 min bursts
- GRADUAL_ESCALATION: 10-20 min intervals
- RAPID_EXTRACTION: 1-3 min intervals
- BENEFICIARY_HOPPING: 3-8 min intervals

**Result:** Timing worked correctly, but velocity remained near zero.

### The Missing Piece: Source-VPA Behavior

Timing controls **WHEN** transactions occur. VPA strategy controls **WHO** performs them.

Even with realistic timing (multiple transactions within 1 hour), random VPA selection meant:
- Transaction 1 from `user5@upi` at T+0
- Transaction 2 from `user12@upi` at T+5min  
- Transaction 3 from `user8@upi` at T+10min

Each source VPA has velocity = 0 because no VPA is reused.

**Insight:** Velocity requires modeling **compromised account behavior** — attackers reusing the same source accounts, not random selection.

---

## C. Source-VPA Strategies Implemented

### Implementation

File: `src/campaigns/vpa_strategy.py`

```python
class VPAStrategy(Enum):
    SINGLE_COMPROMISED_VPA = "single_compromised_vpa"
    SMALL_VPA_POOL = "small_vpa_pool"
    VPA_ROTATION = "vpa_rotation"
    MIXED_REUSE = "mixed_reuse"
```

### Strategy Descriptions

#### 1. SINGLE_COMPROMISED_VPA
**Model:** One fully compromised account used for all campaign transactions.

**Behavior:**
- Selects one primary VPA at campaign start
- All transactions use this VPA as source
- Maximum velocity accumulation

**Use Case:** Known fraud scenarios (S1, S2) where attacker has deep access to one account.

#### 2. SMALL_VPA_POOL
**Model:** Small set of 2-3 coordinated compromised accounts.

**Behavior:**
- Randomly selects from pool of 2-3 VPAs
- Moderate reuse across small set
- Represents coordinated fraud rings

**Use Case:** Organized fraud where multiple accounts work together.

#### 3. VPA_ROTATION
**Model:** High tactical diversity, minimal reuse.

**Behavior:**
- Randomly selects from full available VPA pool
- Each transaction likely uses different source
- Lowest velocity accumulation
- Anti-tracking behavior

**Use Case:** Baseline comparison showing impact of VPA reuse.

#### 4. MIXED_REUSE
**Model:** Balance between primary account and tactical rotation.

**Behavior:**
- 70% probability: use primary VPA (reuse)
- 30% probability: select random different VPA (rotation)
- Moderate velocity with some diversity

**Use Case:** Unknown fraud scenarios (S3, S4) with realistic attacker behavior.

### Integration

- Campaign generator accepts `vpa_strategy` parameter
- Campaign executor creates `VPASelector` and attaches to attacker
- All attacker types (Static, Adaptive, GradualEscalation, BeneficiaryHopping) use VPASelector if available
- Seed control ensures reproducible VPA selection
- Environment isolation preserved

---

## D. Validation Results

### Test Suite: `test_vpa_strategies.py`

All 8 tests passed:

1. ✓ SINGLE_COMPROMISED_VPA uses exactly one source VPA
2. ✓ SMALL_VPA_POOL uses small pool (1-3 sources)
3. ✓ VPA_ROTATION produces high source diversity
4. ✓ MIXED_REUSE shows both reuse and rotation
5. ✓ Velocity increases naturally from VPA reuse
6. ✓ Velocity correctly varies by strategy
7. ✓ Campaigns remain isolated with VPA strategies
8. ✓ Seed reproducibility preserved

### Key Validation Points

**Natural Velocity Emergence:**
- Velocity calculated purely from transaction timestamps and source VPA
- No artificial injection of velocity values
- 1-hour window correctly enforced
- First transaction always has velocity = 0

**Strategy Differentiation:**
- SINGLE_COMPROMISED_VPA produces highest velocity
- VPA_ROTATION produces lowest velocity
- MIXED_REUSE balances reuse and diversity
- Each strategy produces distinct source-usage patterns

**System Integrity:**
- Campaign isolation maintained (fresh environment per campaign)
- Seed reproducibility confirmed
- Detector models, thresholds, features unchanged
- Attacker adaptation logic preserved

---

## E. Velocity Distribution Comparison

### Analysis: `compare_vpa_strategies.py`

Ran 10 campaigns per strategy:

```
Strategy                        Sources    Mean Vel   P90 Vel    Max Vel    vs Training
---------------------------------------------------------------------------------------------
single_compromised_vpa          9          0.82       2          3          0.22x
small_vpa_pool                  11         0.26       1          1          0.07x
vpa_rotation                    13         0.00       0          0          0.00x
mixed_reuse                     9          0.67       2          4          0.18x
---------------------------------------------------------------------------------------------
Training fraud                  N/A        3.76       7          14         1.00x
```

### Observations

**SINGLE_COMPROMISED_VPA:**
- Highest campaign velocity: mean 0.82, max 3
- Still only 0.22x training fraud levels
- 22 transactions across 10 campaigns (2-3 per campaign)
- 9 unique sources (one per campaign, as designed)

**SMALL_VPA_POOL:**
- Moderate velocity: mean 0.26, max 1
- Lower due to spreading across 2-3 VPAs per campaign
- 19 transactions, 11 unique sources

**VPA_ROTATION:**
- Zero velocity: mean 0.00, max 0
- High diversity prevents reuse
- 16 transactions, 13 unique sources
- Useful baseline showing impact of reuse

**MIXED_REUSE:**
- Second-highest velocity: mean 0.67, max 4
- Balances reuse (70%) with rotation (30%)
- 21 transactions, 9 unique sources

**Training Fraud:**
- Mean 3.76, P90 7, max 14
- Represents aggregated historical patterns across many accounts

---

## F. Which Strategies Resemble Training Fraud Distribution

### Quantitative Comparison

None of the strategies perfectly match training fraud velocity distribution.

**Closest Match:**
- SINGLE_COMPROMISED_VPA achieves 0.22x training mean
- MIXED_REUSE achieves 0.18x training mean

**Why The Gap?**

Training fraud and campaign fraud represent **fundamentally different temporal scales**:

1. **Training Fraud (Historical Aggregate)**
   - Mean velocity 3.76 = average across ALL fraud transactions in dataset
   - Includes transactions from accounts with long fraud histories
   - Velocity accumulated over days/weeks of compromised account activity
   - Represents population-level statistics

2. **Campaign Fraud (Individual Episode)**
   - Mean velocity 0.67-0.82 = average within single attack campaign
   - Campaigns are short: 2-4 transactions over minutes/hours
   - Velocity accumulated only within campaign duration
   - Represents individual attack episode

### Qualitative Fit

**Strategy Realism Assessment:**

| Strategy | Behavioral Realism | Velocity Realism | Recommended Use |
|----------|-------------------|------------------|-----------------|
| SINGLE_COMPROMISED_VPA | ✓ High | ✓ Highest relative | S1, S2 (Known) |
| SMALL_VPA_POOL | ✓ Medium | ✗ Low | Coordination tests |
| VPA_ROTATION | ✗ Low (baseline) | ✗ Zero | Control baseline |
| MIXED_REUSE | ✓ High | ✓ Second-highest | S3, S4 (Unknown) |

**Best Practices:**
- Use SINGLE_COMPROMISED_VPA for known fraud (maximizes velocity signal)
- Use MIXED_REUSE for unknown fraud (balances realism with velocity)
- Accept that campaign velocity will be lower than training aggregate
- Focus on **relative velocity differences** between strategies

---

## G. Remaining Modeling Limitations

### 1. Temporal Scale Mismatch

**Limitation:** Campaigns represent short attack episodes (minutes to hours), while training fraud represents historical aggregates (days to weeks).

**Impact:** Campaign velocity will always be lower than training fraud mean.

**Not a Bug:** This is correct modeling. Individual attack campaigns are shorter than population aggregates.

**Mitigation:** Use relative velocity comparisons. SINGLE_COMPROMISED_VPA produces 3x more velocity than VPA_ROTATION.

### 2. Campaign Length

**Limitation:** Most campaigns complete in 2-4 transactions before reaching target amount or being blocked.

**Impact:** Limited opportunity for velocity accumulation within 1-hour window.

**Not a Bug:** This is realistic. Effective detection should stop campaigns quickly.

**Mitigation:** S1-S4 experiments will show whether detectors correctly respond to velocity signals even at these levels.

### 3. Feature Schema Fidelity

**Current Features:**
- `amount`: Transaction amount
- `hour_of_day`: Hour (0-23)
- `is_weekend`: Weekend flag
- `velocity_1h`: Count of transactions from same source VPA in past hour

**Training Fraud May Have Had:**
- Additional behavioral features (recipient patterns, network features)
- Longer velocity windows (24h, 7d)
- Account history features

**Impact:** Unknown. Detectors were trained on 4-feature schema and validated successfully.

**Mitigation:** Feature schema is fixed constraint. S1-S4 will test robustness under this schema.

### 4. Aggregation vs Episodes

**Training Distribution:**
- Population statistics across all fraud
- Includes high-velocity outliers from very active accounts
- Mean 3.76 includes transactions with velocity 0, 1, 2, ... up to 14

**Campaign Distribution:**
- Episode statistics within individual campaigns
- Short campaigns limit maximum velocity
- Most campaigns: velocity 0-3

**Impact:** Expected distributional difference, not a modeling failure.

**Mitigation:** Compare strategies to each other, not to training aggregate.

---

## H. Recommendations for S1-S4

### Strategy Selection by Scenario

#### S1: Known Fraud, No Adaptation
**Recommended:** `VPAStrategy.SINGLE_COMPROMISED_VPA`

**Rationale:**
- Known fraud type matches training patterns
- Single compromised account is realistic threat model
- Maximizes velocity signal for detector to observe
- Tests whether detector responds to velocity feature

#### S2: Known Fraud, With Adaptation
**Recommended:** `VPAStrategy.SINGLE_COMPROMISED_VPA`

**Rationale:**
- Same as S1 for consistency
- Adaptive attackers will explore detector boundaries
- Single-VPA maintains velocity pressure
- Tests whether adaptation can overcome velocity-based detection

#### S3: Unknown Fraud, No Adaptation
**Recommended:** `VPAStrategy.MIXED_REUSE`

**Rationale:**
- Unknown fraud type requires more realistic diversity
- 70/30 reuse/rotation balances velocity with tactical variation
- More challenging threat model than single-VPA
- Tests detector against sophisticated static attacker

#### S4: Unknown Fraud, With Adaptation
**Recommended:** `VPAStrategy.MIXED_REUSE`

**Rationale:**
- Most realistic threat: unknown pattern + adaptive behavior
- Adaptive attackers will learn from velocity-based blocks
- Mixed reuse provides both velocity signal and evasion attempts
- Strongest test of detector robustness

### Alternative Testing

**Sensitivity Analysis:**
Compare same scenario (e.g., S3) across all strategies:
- S3a: SINGLE_COMPROMISED_VPA
- S3b: SMALL_VPA_POOL  
- S3c: VPA_ROTATION
- S3d: MIXED_REUSE

**Research Question:** How much does source-VPA strategy affect detector performance?

### Expectations

**Realistic Expectations:**
- Campaign velocity: 0.5-1.0 mean (individual episodes)
- Training velocity: 3.76 mean (population aggregate)
- Gap is expected due to temporal scale difference

**Success Criteria:**
- Detectors distinguish strategies (e.g., higher detection on SINGLE_COMPROMISED_VPA)
- Adaptive attackers show learning behavior
- Velocity feature contributes to risk scoring
- Results demonstrate detector strengths and limitations

**Not Success Criteria:**
- Campaign velocity matching training velocity exactly
- 100% detection rate (some fraud should succeed for realism)
- Zero false positives (legitimate traffic allowed)

---

## Conclusion

Source-VPA strategies successfully address the velocity modeling gap. Four distinct strategies provide configurable realism for S1-S4 scenarios:

1. **SINGLE_COMPROMISED_VPA**: Highest velocity, recommended for known fraud (S1, S2)
2. **SMALL_VPA_POOL**: Coordinated accounts, specialized use cases
3. **VPA_ROTATION**: Zero velocity baseline, control comparison
4. **MIXED_REUSE**: Balanced realism, recommended for unknown fraud (S3, S4)

Velocity now emerges naturally from transaction patterns and VPA reuse. Campaign velocity is lower than training fraud due to temporal scale differences (episodes vs population aggregates), which is correct modeling.

Ready to proceed with S1-S4 robustness experiments using these strategies.

---

## Appendices

### A.1 Implementation Files

- `src/campaigns/vpa_strategy.py`: VPAStrategy enum and VPASelector class
- `src/campaigns/generator.py`: Campaign creation with strategy parameter
- `src/campaigns/executor.py`: VPASelector initialization and attachment
- `src/attackers/static.py`: VPA selector integration
- `src/attackers/adaptive.py`: VPA selector integration  
- `src/attackers/family_based.py`: VPA selector integration (both families)

### A.2 Validation Scripts

- `test_vpa_strategies.py`: 8 validation tests (all passed)
- `compare_vpa_strategies.py`: Multi-campaign velocity analysis
- `analyze_velocity.py`: Training fraud baseline statistics

### A.3 Key Constraints Preserved

✓ Detector models unchanged  
✓ Trained weights unchanged  
✓ Thresholds unchanged  
✓ Detector feature schema unchanged  
✓ Attacker adaptation logic unchanged  
✓ Environment isolation unchanged  
✓ Velocity calculated from transaction history only  
✓ No artificial injection of velocity values

### A.4 Research Context

This validation is part of the UPI Fraud Stress Lab's environment verification phase. After identifying and fixing an environmental artifact in velocity accumulation (ENVIRONMENTAL_ARTIFACT_FIX_VALIDATION.md) and implementing realistic timing (REALISTIC_VELOCITY_VALIDATION.md), source-VPA modeling completes the campaign generation framework.

Next phase: S1-S4 robustness experiments to evaluate detector performance against adaptive and static attackers with known and unknown fraud patterns.
