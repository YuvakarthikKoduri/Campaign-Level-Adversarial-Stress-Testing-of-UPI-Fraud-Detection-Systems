#!/usr/bin/env python3
"""
Compare VPA strategies and their impact on velocity distribution.

Tests each strategy:
1. SINGLE_COMPROMISED_VPA - one source for all transactions
2. SMALL_VPA_POOL - 2-3 sources rotated
3. VPA_ROTATION - random selection from large pool
4. MIXED_REUSE - 70% primary, 30% rotation

Reports:
- Unique source VPAs
- Transactions per source
- Velocity distribution (mean, median, P90, P99, max)
- Comparison to training fraud (mean 3.76, P90 7)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from collections import Counter
from datetime import datetime
from src.campaigns.generator import CampaignGenerator
from src.campaigns.vpa_strategy import VPAStrategy
from src.campaigns.executor import CampaignExecutor
from src.attackers.static import StaticAttacker
from src.attackers.adaptive import AdaptiveAttacker
from src.environment import UPIEnvironment
from src.detectors.baseline import BaselineDetector
import pandas as pd


def analyze_strategy(strategy, num_campaigns=10, seed_base=1000):
    """Analyze a VPA strategy across multiple campaigns."""
    detector = BaselineDetector('models/baseline_xgboost.pkl')
    generator = CampaignGenerator()
    accounts = [f"user{i}@upi" for i in range(20)]

    all_transactions = []
    all_velocities = []
    source_vpa_usage = Counter()

    for i in range(num_campaigns):
        env = UPIEnvironment(fraud_detector=detector)

        # Create campaign with specified strategy
        campaign = generator.create_known_fraud_campaign(
            target_amount=30000,
            vpa_strategy=strategy
        )

        attacker = StaticAttacker(fraud_type="known")
        executor = CampaignExecutor(detector, env, attacker)

        completed = executor.execute_campaign(campaign, accounts, seed=seed_base + i)

        for txn in completed.transactions:
            source = txn.get('from_vpa')
            velocity = txn.get('features', {}).get('velocity_1h', 0)

            source_vpa_usage[source] += 1
            all_velocities.append(velocity)
            all_transactions.append({
                'campaign_id': campaign.campaign_id,
                'from_vpa': source,
                'velocity': velocity,
                'amount': txn.get('amount', 0),
                'risk_score': txn.get('risk_score', 0)
            })

    # Calculate statistics
    unique_sources = len(source_vpa_usage)
    total_txns = len(all_velocities)

    sorted_velocities = sorted(all_velocities)
    mean_velocity = sum(all_velocities) / len(all_velocities) if all_velocities else 0
    median_velocity = sorted_velocities[len(sorted_velocities) // 2] if sorted_velocities else 0
    p90_velocity = sorted_velocities[int(len(sorted_velocities) * 0.9)] if sorted_velocities else 0
    p99_velocity = sorted_velocities[int(len(sorted_velocities) * 0.99)] if sorted_velocities else 0
    max_velocity = max(all_velocities) if all_velocities else 0

    return {
        'strategy': strategy,
        'num_campaigns': num_campaigns,
        'total_transactions': total_txns,
        'unique_sources': unique_sources,
        'source_usage': dict(source_vpa_usage.most_common(5)),
        'velocities': all_velocities,
        'mean_velocity': mean_velocity,
        'median_velocity': median_velocity,
        'p90_velocity': p90_velocity,
        'p99_velocity': p99_velocity,
        'max_velocity': max_velocity,
        'velocity_distribution': dict(Counter(all_velocities))
    }


def main():
    """Compare all VPA strategies."""
    print("="*80)
    print("SOURCE VPA STRATEGY COMPARISON")
    print("="*80)

    # Load training fraud for comparison
    training_df = pd.read_csv('data/synthetic/upi_transactions_v1.csv')
    training_fraud = training_df[training_df['is_fraud'] == 1]

    print("\nTRAINING FRAUD BASELINE:")
    print(f"  Mean velocity: {training_fraud['velocity_1h'].mean():.2f}")
    print(f"  Median velocity: {training_fraud['velocity_1h'].median():.0f}")
    print(f"  P90 velocity: {training_fraud['velocity_1h'].quantile(0.90):.0f}")
    print(f"  Max velocity: {training_fraud['velocity_1h'].max():.0f}")

    strategies = [
        VPAStrategy.SINGLE_COMPROMISED_VPA,
        VPAStrategy.SMALL_VPA_POOL,
        VPAStrategy.VPA_ROTATION,
        VPAStrategy.MIXED_REUSE
    ]

    results = {}

    for strategy in strategies:
        print(f"\n{'='*80}")
        print(f"STRATEGY: {strategy.value.upper()}")
        print("="*80)

        result = analyze_strategy(strategy, num_campaigns=10, seed_base=2000)
        results[strategy] = result

        print(f"\nCampaigns: {result['num_campaigns']}")
        print(f"Total transactions: {result['total_transactions']}")
        print(f"Unique source VPAs: {result['unique_sources']}")
        print(f"\nSource VPA usage (top 5):")
        for vpa, count in result['source_usage'].items():
            print(f"  {vpa}: {count} transactions ({count/result['total_transactions']*100:.1f}%)")

        print(f"\nVelocity Statistics:")
        print(f"  Mean: {result['mean_velocity']:.2f}")
        print(f"  Median: {result['median_velocity']:.0f}")
        print(f"  P90: {result['p90_velocity']:.0f}")
        print(f"  P99: {result['p99_velocity']:.0f}")
        print(f"  Max: {result['max_velocity']:.0f}")

        print(f"\nVelocity Distribution:")
        vel_dist = result['velocity_distribution']
        for v in sorted(vel_dist.keys())[:10]:  # Show first 10
            print(f"  velocity={v}: {vel_dist[v]} transactions ({vel_dist[v]/result['total_transactions']*100:.1f}%)")

    # Comparison table
    print("\n" + "="*80)
    print("STRATEGY COMPARISON TABLE")
    print("="*80)

    training_mean = training_fraud['velocity_1h'].mean()
    training_p90 = training_fraud['velocity_1h'].quantile(0.90)

    print(f"\n{'Strategy':<30} {'Sources':<10} {'Mean Vel':<10} {'P90 Vel':<10} {'Max Vel':<10} {'vs Training':<15}")
    print("-"*90)

    for strategy in strategies:
        r = results[strategy]
        vs_training = f"{r['mean_velocity']/training_mean:.2f}x" if training_mean > 0 else "N/A"
        print(f"{strategy.value:<30} {r['unique_sources']:<10} {r['mean_velocity']:<10.2f} "
              f"{r['p90_velocity']:<10.0f} {r['max_velocity']:<10.0f} {vs_training:<15}")

    print(f"{'Training fraud':<30} {'N/A':<10} {training_mean:<10.2f} "
          f"{training_p90:<10.0f} {training_fraud['velocity_1h'].max():<10.0f} {'1.00x':<15}")

    # Recommendations
    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)

    print("""
Strategy Selection Guidelines:

1. SINGLE_COMPROMISED_VPA (RECOMMENDED for Known Fraud)
   - Best matches training fraud model
   - Highest velocity accumulation
   - Represents compromised account behavior
   - Use for: S1, S2 (Known fraud scenarios)

2. SMALL_VPA_POOL
   - Moderate velocity, coordinated accounts
   - Multiple compromised accounts working together
   - Use for: Testing detector against organized fraud rings

3. VPA_ROTATION
   - Lowest velocity, high source diversity
   - Anti-tracking tactical behavior
   - Use for: Baseline comparison (shows impact of VPA reuse)

4. MIXED_REUSE (RECOMMENDED for Unknown Fraud)
   - Balance between velocity and diversity
   - More realistic attacker behavior (both tactics)
   - Use for: S3, S4 (Unknown fraud scenarios)

NOTE: None of the strategies perfectly match training fraud velocity distribution.
Training fraud represents AGGREGATED historical patterns across many compromised
accounts. Campaigns represent INDIVIDUAL attack episodes. This is a fundamental
modeling difference, not a bug.
""")

    print("="*80)


if __name__ == "__main__":
    main()
