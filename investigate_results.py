#!/usr/bin/env python3
"""
Scientific investigation of experimental results.

Traces complete campaign trajectories to understand:
- Why S4 achieves 0% success for both detectors
- Why S1 achieves 100% success for both detectors
- What adaptive attackers actually change
- Whether adaptations help or hurt success
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import random
import numpy as np
from src.detectors.baseline import load_detector
from src.environment import UPIEnvironment
from src.campaigns.generator import CampaignGenerator, CampaignFamily
from src.campaigns.executor import CampaignExecutor
from src.attackers.static import StaticAttacker
from src.attackers.adaptive import AdaptiveAttacker


def trace_campaign_trajectory(campaign, attacker, detector, environment, accounts, max_steps=20, verbose=True):
    """
    Trace a complete campaign trajectory with detailed logging.

    Returns detailed transaction-by-transaction data.
    """
    executor = CampaignExecutor(detector, environment, attacker, max_steps=max_steps)

    if verbose:
        print(f"\n{'='*80}")
        print(f"CAMPAIGN TRACE: {campaign.family.value}")
        print(f"{'='*80}")
        print(f"Target: ₹{campaign.target_amount:,.0f}")
        print(f"Attacker: {attacker.__class__.__name__}")
        print(f"Max steps: {max_steps}")
        print()

    trajectory = []

    result = executor.execute_campaign(campaign, accounts, verbose=False)

    for i, txn in enumerate(result.transactions):
        step_data = {
            'step': i + 1,
            'family': campaign.family.value,
            'amount': txn['amount'],
            'from_vpa': txn['from_vpa'],
            'to_vpa': txn['to_vpa'],
            'hour_of_day': txn.get('hour_of_day', 0),
            'velocity_1h': txn.get('velocity_1h', 0),
            'is_new_vpa': txn.get('is_new_vpa', 1),
            'risk_score': txn.get('risk_score', 0),
            'decision': txn.get('decision', 'UNKNOWN'),
        }

        if verbose:
            print(f"Step {i+1}:")
            print(f"  Amount: ₹{txn['amount']:,.2f}")
            print(f"  Features: hour={txn.get('hour_of_day', 0)}, velocity={txn.get('velocity_1h', 0)}, new_vpa={txn.get('is_new_vpa', 1)}")
            print(f"  Risk Score: {txn.get('risk_score', 0):.4f}")
            print(f"  Decision: {txn.get('decision', 'UNKNOWN')}")

            if isinstance(attacker, AdaptiveAttacker):
                summary = attacker.get_adaptation_summary()
                print(f"  Attacker State: allowed={summary['allowed_count']}, blocked={summary['blocked_count']}, adaptations={summary['adaptation_count']}")
            print()

        trajectory.append(step_data)

    if verbose:
        print(f"Final Result:")
        print(f"  Status: {result.status.value}")
        print(f"  Amount Moved: ₹{result.total_amount_moved:,.2f}")
        print(f"  Success: {result.total_amount_moved >= campaign.target_amount}")
        print()

    return {
        'campaign_id': campaign.campaign_id,
        'family': campaign.family.value,
        'target': campaign.target_amount,
        'attacker_type': attacker.__class__.__name__,
        'trajectory': trajectory,
        'final_status': result.status.value,
        'amount_moved': result.total_amount_moved,
        'success': result.total_amount_moved >= campaign.target_amount
    }


def compare_static_vs_adaptive_same_campaign(seed, detector_name="xgboost"):
    """
    Compare static vs adaptive for the SAME campaign seed.
    """
    print(f"\n{'='*80}")
    print(f"STATIC VS ADAPTIVE COMPARISON (seed={seed}, detector={detector_name})")
    print(f"{'='*80}")

    # Load detector
    if detector_name == "xgboost":
        detector = load_detector('models/baseline_xgboost.pkl')
    else:
        detector = load_detector('models/baseline_random_forest.pkl')

    accounts = [f"user{i}@upi" for i in range(20)]

    # S3: Unknown + Static
    random.seed(seed)
    np.random.seed(seed)
    environment_static = UPIEnvironment(fraud_detector=detector)
    generator_static = CampaignGenerator()
    campaign_static = generator_static.create_unknown_fraud_campaign(target_amount=15000)
    attacker_static = StaticAttacker(fraud_type="unknown")

    print("\n--- S3: Unknown + Static ---")
    trace_static = trace_campaign_trajectory(
        campaign_static, attacker_static, detector, environment_static, accounts, max_steps=20, verbose=True
    )

    # S4: Unknown + Adaptive (same seed, same campaign family)
    random.seed(seed)
    np.random.seed(seed)
    environment_adaptive = UPIEnvironment(fraud_detector=detector)
    generator_adaptive = CampaignGenerator()
    campaign_adaptive = generator_adaptive.create_unknown_fraud_campaign(target_amount=15000)
    attacker_adaptive = AdaptiveAttacker(fraud_type="unknown")

    print("\n--- S4: Unknown + Adaptive ---")
    trace_adaptive = trace_campaign_trajectory(
        campaign_adaptive, attacker_adaptive, detector, environment_adaptive, accounts, max_steps=20, verbose=True
    )

    # Compare
    print(f"\n{'='*80}")
    print("COMPARISON SUMMARY")
    print(f"{'='*80}")
    print(f"Campaign Family: {trace_static['family']} (both)")
    print(f"\nStatic:")
    print(f"  Amount moved: ₹{trace_static['amount_moved']:,.2f}")
    print(f"  Success: {trace_static['success']}")
    print(f"  Transactions: {len(trace_static['trajectory'])}")

    print(f"\nAdaptive:")
    print(f"  Amount moved: ₹{trace_adaptive['amount_moved']:,.2f}")
    print(f"  Success: {trace_adaptive['success']}")
    print(f"  Transactions: {len(trace_adaptive['trajectory'])}")

    # Transaction-level comparison
    print(f"\nTransaction-by-Transaction Comparison:")
    print(f"{'Step':<6} {'Static Amount':<15} {'Adaptive Amount':<15} {'Static Risk':<12} {'Adaptive Risk':<12} {'Static Dec':<10} {'Adaptive Dec':<10}")
    print("-" * 90)

    max_txns = max(len(trace_static['trajectory']), len(trace_adaptive['trajectory']))
    for i in range(max_txns):
        static_txn = trace_static['trajectory'][i] if i < len(trace_static['trajectory']) else None
        adaptive_txn = trace_adaptive['trajectory'][i] if i < len(trace_adaptive['trajectory']) else None

        static_amt = f"₹{static_txn['amount']:,.0f}" if static_txn else "-"
        adaptive_amt = f"₹{adaptive_txn['amount']:,.0f}" if adaptive_txn else "-"
        static_risk = f"{static_txn['risk_score']:.4f}" if static_txn else "-"
        adaptive_risk = f"{adaptive_txn['risk_score']:.4f}" if adaptive_txn else "-"
        static_dec = static_txn['decision'] if static_txn else "-"
        adaptive_dec = adaptive_txn['decision'] if adaptive_txn else "-"

        print(f"{i+1:<6} {static_amt:<15} {adaptive_amt:<15} {static_risk:<12} {adaptive_risk:<12} {static_dec:<10} {adaptive_dec:<10}")

    return trace_static, trace_adaptive


def investigate_s4_zero_success(detector_name="xgboost", num_trials=5):
    """
    Investigate why S4 achieves 0% success.

    Check:
    - Are campaigns hitting max_steps?
    - Are amounts too conservative?
    - Is adaptation making things worse?
    - Are detector features catching unknown patterns?
    """
    print(f"\n{'='*80}")
    print(f"INVESTIGATING S4 ZERO SUCCESS ({detector_name})")
    print(f"{'='*80}")

    if detector_name == "xgboost":
        detector = load_detector('models/baseline_xgboost.pkl')
    else:
        detector = load_detector('models/baseline_random_forest.pkl')

    accounts = [f"user{i}@upi" for i in range(20)]

    failure_reasons = []

    for trial in range(num_trials):
        seed = 100 + trial
        random.seed(seed)
        np.random.seed(seed)

        environment = UPIEnvironment(fraud_detector=detector)
        generator = CampaignGenerator()
        campaign = generator.create_unknown_fraud_campaign(target_amount=15000)
        attacker = AdaptiveAttacker(fraud_type="unknown")

        print(f"\nTrial {trial + 1} (seed={seed}, family={campaign.family.value}):")

        trace = trace_campaign_trajectory(
            campaign, attacker, detector, environment, accounts, max_steps=50, verbose=False
        )

        # Analyze failure
        blocked_count = sum(1 for txn in trace['trajectory'] if txn['decision'] == 'BLOCK')
        flagged_count = sum(1 for txn in trace['trajectory'] if txn['decision'] == 'FLAG')
        allowed_count = sum(1 for txn in trace['trajectory'] if txn['decision'] == 'ALLOW')

        avg_risk = np.mean([txn['risk_score'] for txn in trace['trajectory']])
        max_risk = np.max([txn['risk_score'] for txn in trace['trajectory']])

        hit_max_steps = len(trace['trajectory']) >= 50

        print(f"  Result: {trace['final_status']}")
        print(f"  Amount moved: ₹{trace['amount_moved']:,.2f} / ₹{trace['target']:,.2f}")
        print(f"  Transactions: {len(trace['trajectory'])}")
        print(f"  Decisions: ALLOW={allowed_count}, FLAG={flagged_count}, BLOCK={blocked_count}")
        print(f"  Risk scores: avg={avg_risk:.4f}, max={max_risk:.4f}")
        print(f"  Hit max steps: {hit_max_steps}")

        # Determine failure reason
        if blocked_count > 0:
            reason = "BLOCKED_EARLY"
        elif hit_max_steps:
            reason = "MAX_STEPS_REACHED"
        elif allowed_count > 0 and trace['amount_moved'] < trace['target']:
            reason = "INSUFFICIENT_PROGRESS"
        else:
            reason = "OTHER"

        failure_reasons.append(reason)
        print(f"  Failure reason: {reason}")

    print(f"\n{'='*80}")
    print("S4 FAILURE ANALYSIS SUMMARY")
    print(f"{'='*80}")
    from collections import Counter
    reason_counts = Counter(failure_reasons)
    for reason, count in reason_counts.items():
        print(f"  {reason}: {count}/{num_trials} ({count/num_trials*100:.0f}%)")


def investigate_s1_perfect_success(detector_name="xgboost", num_trials=5):
    """
    Investigate why S1 achieves 100% success.

    Check:
    - Are known campaigns unrealistically easy?
    - Do high amounts bypass detection?
    - Are features aligned with training distribution?
    """
    print(f"\n{'='*80}")
    print(f"INVESTIGATING S1 PERFECT SUCCESS ({detector_name})")
    print(f"{'='*80}")

    if detector_name == "xgboost":
        detector = load_detector('models/baseline_xgboost.pkl')
    else:
        detector = load_detector('models/baseline_random_forest.pkl')

    accounts = [f"user{i}@upi" for i in range(20)]

    for trial in range(num_trials):
        seed = 200 + trial
        random.seed(seed)
        np.random.seed(seed)

        environment = UPIEnvironment(fraud_detector=detector)
        generator = CampaignGenerator()
        campaign = generator.create_known_fraud_campaign(target_amount=30000)
        attacker = StaticAttacker(fraud_type="known")

        print(f"\nTrial {trial + 1} (seed={seed}):")

        trace = trace_campaign_trajectory(
            campaign, attacker, detector, environment, accounts, max_steps=20, verbose=False
        )

        # Analyze success
        allowed_count = sum(1 for txn in trace['trajectory'] if txn['decision'] == 'ALLOW')
        avg_risk = np.mean([txn['risk_score'] for txn in trace['trajectory']])
        avg_amount = np.mean([txn['amount'] for txn in trace['trajectory']])

        print(f"  Result: {trace['final_status']}")
        print(f"  Amount moved: ₹{trace['amount_moved']:,.2f} / ₹{trace['target']:,.2f}")
        print(f"  Transactions: {len(trace['trajectory'])} ({allowed_count} allowed)")
        print(f"  Avg risk score: {avg_risk:.4f}")
        print(f"  Avg transaction amount: ₹{avg_amount:,.2f}")
        print(f"  Success: {trace['success']}")


def analyze_campaign_families():
    """
    Analyze all 4 campaign families in detail.
    """
    print(f"\n{'='*80}")
    print("CAMPAIGN FAMILY ANALYSIS")
    print(f"{'='*80}")

    detector = load_detector('models/baseline_xgboost.pkl')
    environment = UPIEnvironment(fraud_detector=detector)
    accounts = [f"user{i}@upi" for i in range(20)]

    families_to_test = [
        ("HIGH_VALUE_BURST", "known", 30000),
        ("SLOW_DRAIN", "unknown", 15000),
        ("GRADUAL_ESCALATION", "unknown", 15000),
        ("BENEFICIARY_HOPPING", "unknown", 15000),
    ]

    family_stats = {}

    for family_name, fraud_type, target in families_to_test:
        print(f"\n{'='*80}")
        print(f"Family: {family_name}")
        print(f"{'='*80}")

        # Generate 5 campaigns from this family
        amounts = []
        risk_scores = []
        allow_rates = []

        for i in range(5):
            random.seed(300 + i)
            np.random.seed(300 + i)

            generator = CampaignGenerator()

            # Force specific family by generating until we get it
            for _ in range(100):
                if fraud_type == "known":
                    campaign = generator.create_known_fraud_campaign(target_amount=target)
                else:
                    campaign = generator.create_unknown_fraud_campaign(target_amount=target)

                if campaign.family.value == family_name.lower():
                    break

            if campaign.family.value != family_name.lower():
                print(f"  Warning: Could not generate {family_name} campaign")
                continue

            attacker = StaticAttacker(fraud_type=fraud_type)
            executor = CampaignExecutor(detector, environment, attacker, max_steps=10)
            result = executor.execute_campaign(campaign, accounts, verbose=False)

            # Collect statistics
            for txn in result.transactions:
                amounts.append(txn['amount'])
                risk_scores.append(txn.get('risk_score', 0))

            allowed = sum(1 for txn in result.transactions if txn.get('decision') == 'ALLOW')
            allow_rates.append(allowed / len(result.transactions) if result.transactions else 0)

        if amounts:
            family_stats[family_name] = {
                'amount_mean': np.mean(amounts),
                'amount_std': np.std(amounts),
                'amount_min': np.min(amounts),
                'amount_max': np.max(amounts),
                'risk_mean': np.mean(risk_scores),
                'risk_std': np.std(risk_scores),
                'allow_rate': np.mean(allow_rates)
            }

            print(f"  Amount Distribution:")
            print(f"    Mean: ₹{family_stats[family_name]['amount_mean']:,.2f}")
            print(f"    Std: ₹{family_stats[family_name]['amount_std']:,.2f}")
            print(f"    Range: ₹{family_stats[family_name]['amount_min']:,.2f} - ₹{family_stats[family_name]['amount_max']:,.2f}")
            print(f"  Risk Score Distribution:")
            print(f"    Mean: {family_stats[family_name]['risk_mean']:.4f}")
            print(f"    Std: {family_stats[family_name]['risk_std']:.4f}")
            print(f"  Average Allow Rate: {family_stats[family_name]['allow_rate']:.1%}")

    return family_stats


def main():
    print("="*80)
    print("SCIENTIFIC INVESTIGATION OF EXPERIMENTAL RESULTS")
    print("="*80)

    # 1. Compare static vs adaptive for same campaign
    print("\n\n" + "="*80)
    print("INVESTIGATION 1: Static vs Adaptive (Same Campaign)")
    print("="*80)
    compare_static_vs_adaptive_same_campaign(seed=42, detector_name="xgboost")

    # 2. Investigate S4 zero success
    print("\n\n" + "="*80)
    print("INVESTIGATION 2: Why S4 Achieves 0% Success")
    print("="*80)
    investigate_s4_zero_success(detector_name="xgboost", num_trials=5)

    # 3. Investigate S1 perfect success
    print("\n\n" + "="*80)
    print("INVESTIGATION 3: Why S1 Achieves 100% Success")
    print("="*80)
    investigate_s1_perfect_success(detector_name="xgboost", num_trials=5)

    # 4. Analyze campaign families
    print("\n\n" + "="*80)
    print("INVESTIGATION 4: Campaign Family Characteristics")
    print("="*80)
    analyze_campaign_families()

    print("\n\n" + "="*80)
    print("INVESTIGATION COMPLETE")
    print("="*80)
    print("\nSee output above for detailed traces and analysis.")
    print("Next: Run multi-seed experiments for statistical validation.")


if __name__ == "__main__":
    main()
