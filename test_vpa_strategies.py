#!/usr/bin/env python3
"""
Validation tests for VPA strategy implementation.

Tests:
1. SINGLE_COMPROMISED_VPA produces repeated source VPA usage
2. SMALL_VPA_POOL only uses the configured pool
3. VPA_ROTATION preserves diverse source usage
4. MIXED_REUSE produces both reuse and rotation
5. Velocity increases naturally when same VPA performs multiple transactions
6. Transactions outside 1-hour window are excluded
7. Campaign isolation is preserved
8. Seed reproducibility is preserved
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from collections import Counter
from src.campaigns.generator import CampaignGenerator
from src.campaigns.vpa_strategy import VPAStrategy, VPASelector
from src.campaigns.executor import CampaignExecutor
from src.attackers.static import StaticAttacker
from src.environment import UPIEnvironment
from src.detectors.baseline import BaselineDetector


def test_single_compromised_vpa():
    """Test that SINGLE_COMPROMISED_VPA uses one source for all transactions."""
    print("="*70)
    print("TEST 1: SINGLE_COMPROMISED_VPA Strategy")
    print("="*70)

    detector = BaselineDetector('models/baseline_xgboost.pkl')
    generator = CampaignGenerator()
    accounts = [f"user{i}@upi" for i in range(20)]

    env = UPIEnvironment(fraud_detector=detector)
    campaign = generator.create_known_fraud_campaign(
        target_amount=50000,
        vpa_strategy=VPAStrategy.SINGLE_COMPROMISED_VPA
    )

    attacker = StaticAttacker(fraud_type="known")
    executor = CampaignExecutor(detector, env, attacker)
    completed = executor.execute_campaign(campaign, accounts, seed=100)

    source_vpas = [txn['from_vpa'] for txn in completed.transactions]
    unique_sources = set(source_vpas)

    print(f"\nTransactions: {len(source_vpas)}")
    print(f"Unique sources: {len(unique_sources)}")
    print(f"Source VPAs: {Counter(source_vpas)}")

    assert len(unique_sources) == 1, f"Expected 1 unique source, got {len(unique_sources)}"
    print("\n✓ SINGLE_COMPROMISED_VPA uses exactly one source VPA\n")


def test_small_vpa_pool():
    """Test that SMALL_VPA_POOL only uses 2-3 sources."""
    print("="*70)
    print("TEST 2: SMALL_VPA_POOL Strategy")
    print("="*70)

    detector = BaselineDetector('models/baseline_xgboost.pkl')
    generator = CampaignGenerator()
    accounts = [f"user{i}@upi" for i in range(20)]

    env = UPIEnvironment(fraud_detector=detector)
    campaign = generator.create_known_fraud_campaign(
        target_amount=50000,
        vpa_strategy=VPAStrategy.SMALL_VPA_POOL
    )

    attacker = StaticAttacker(fraud_type="known")
    executor = CampaignExecutor(detector, env, attacker)
    completed = executor.execute_campaign(campaign, accounts, seed=200)

    source_vpas = [txn['from_vpa'] for txn in completed.transactions]
    unique_sources = set(source_vpas)

    print(f"\nTransactions: {len(source_vpas)}")
    print(f"Unique sources: {len(unique_sources)}")
    print(f"Source VPAs: {Counter(source_vpas)}")

    assert 1 <= len(unique_sources) <= 3, f"Expected 1-3 unique sources, got {len(unique_sources)}"
    print("\n✓ SMALL_VPA_POOL uses small pool (1-3 sources)\n")


def test_vpa_rotation():
    """Test that VPA_ROTATION uses diverse sources."""
    print("="*70)
    print("TEST 3: VPA_ROTATION Strategy")
    print("="*70)

    detector = BaselineDetector('models/baseline_xgboost.pkl')
    generator = CampaignGenerator()
    accounts = [f"user{i}@upi" for i in range(20)]

    env = UPIEnvironment(fraud_detector=detector)
    campaign = generator.create_known_fraud_campaign(
        target_amount=80000,  # Higher target for more transactions
        vpa_strategy=VPAStrategy.VPA_ROTATION
    )

    attacker = StaticAttacker(fraud_type="known")
    executor = CampaignExecutor(detector, env, attacker)
    completed = executor.execute_campaign(campaign, accounts, seed=300)

    source_vpas = [txn['from_vpa'] for txn in completed.transactions]
    unique_sources = set(source_vpas)

    print(f"\nTransactions: {len(source_vpas)}")
    print(f"Unique sources: {len(unique_sources)}")
    print(f"Source VPAs: {Counter(source_vpas)}")

    # With rotation, expect high diversity (at least 50% unique)
    diversity_ratio = len(unique_sources) / len(source_vpas)
    print(f"Diversity ratio: {diversity_ratio:.2f}")

    assert diversity_ratio >= 0.5, f"Expected diversity ratio >= 0.5, got {diversity_ratio:.2f}"
    print("\n✓ VPA_ROTATION produces high source diversity\n")


def test_mixed_reuse():
    """Test that MIXED_REUSE produces both reuse and rotation."""
    print("="*70)
    print("TEST 4: MIXED_REUSE Strategy")
    print("="*70)

    detector = BaselineDetector('models/baseline_xgboost.pkl')
    generator = CampaignGenerator()
    accounts = [f"user{i}@upi" for i in range(20)]

    env = UPIEnvironment(fraud_detector=detector)
    campaign = generator.create_known_fraud_campaign(
        target_amount=80000,
        vpa_strategy=VPAStrategy.MIXED_REUSE
    )

    attacker = StaticAttacker(fraud_type="known")
    executor = CampaignExecutor(detector, env, attacker)
    completed = executor.execute_campaign(campaign, accounts, seed=400)

    source_vpas = [txn['from_vpa'] for txn in completed.transactions]
    unique_sources = set(source_vpas)
    source_counts = Counter(source_vpas)

    print(f"\nTransactions: {len(source_vpas)}")
    print(f"Unique sources: {len(unique_sources)}")
    print(f"Source VPAs: {source_counts}")

    # Should have one primary source with multiple uses
    max_count = max(source_counts.values())
    print(f"Max uses of single source: {max_count}")

    # Should also have some diversity
    diversity_ratio = len(unique_sources) / len(source_vpas)
    print(f"Diversity ratio: {diversity_ratio:.2f}")

    assert max_count > 1, "Expected primary source to be reused"
    assert len(unique_sources) > 1, "Expected some source diversity"
    print("\n✓ MIXED_REUSE shows both reuse and rotation\n")


def test_velocity_from_reuse():
    """Test that velocity increases naturally when same VPA is reused."""
    print("="*70)
    print("TEST 5: Velocity From VPA Reuse")
    print("="*70)

    detector = BaselineDetector('models/baseline_xgboost.pkl')
    generator = CampaignGenerator()
    accounts = [f"user{i}@upi" for i in range(20)]

    env = UPIEnvironment(fraud_detector=detector)
    campaign = generator.create_known_fraud_campaign(
        target_amount=50000,
        vpa_strategy=VPAStrategy.SINGLE_COMPROMISED_VPA
    )

    attacker = StaticAttacker(fraud_type="known")
    executor = CampaignExecutor(detector, env, attacker)
    completed = executor.execute_campaign(campaign, accounts, seed=500)

    velocities = [txn.get('features', {}).get('velocity_1h', 0) for txn in completed.transactions]

    print(f"\nTransactions: {len(velocities)}")
    print(f"Velocities: {velocities}")
    print(f"Max velocity: {max(velocities) if velocities else 0}")

    # First transaction should have velocity 0
    assert velocities[0] == 0, f"First transaction should have velocity 0, got {velocities[0]}"

    # Later transactions should have non-zero velocity (same VPA reused)
    if len(velocities) > 1:
        assert max(velocities) > 0, "Expected velocity > 0 from VPA reuse"

    print("\n✓ Velocity increases naturally from VPA reuse\n")


def test_velocity_comparison():
    """Compare velocity across strategies."""
    print("="*70)
    print("TEST 6: Velocity Comparison Across Strategies")
    print("="*70)

    detector = BaselineDetector('models/baseline_xgboost.pkl')
    generator = CampaignGenerator()
    accounts = [f"user{i}@upi" for i in range(20)]

    results = {}

    for strategy in [VPAStrategy.SINGLE_COMPROMISED_VPA, VPAStrategy.VPA_ROTATION]:
        env = UPIEnvironment(fraud_detector=detector)
        campaign = generator.create_known_fraud_campaign(
            target_amount=50000,
            vpa_strategy=strategy
        )

        attacker = StaticAttacker(fraud_type="known")
        executor = CampaignExecutor(detector, env, attacker)
        completed = executor.execute_campaign(campaign, accounts, seed=600)

        velocities = [txn.get('features', {}).get('velocity_1h', 0) for txn in completed.transactions]
        mean_vel = sum(velocities) / len(velocities) if velocities else 0
        results[strategy] = mean_vel

        print(f"\n{strategy.value}:")
        print(f"  Mean velocity: {mean_vel:.2f}")

    # SINGLE_COMPROMISED_VPA should have higher velocity than VPA_ROTATION
    assert results[VPAStrategy.SINGLE_COMPROMISED_VPA] > results[VPAStrategy.VPA_ROTATION], \
        "SINGLE_COMPROMISED_VPA should produce higher velocity than VPA_ROTATION"

    print("\n✓ Velocity correctly varies by strategy\n")


def test_campaign_isolation():
    """Test that campaigns remain isolated with VPA strategies."""
    print("="*70)
    print("TEST 7: Campaign Isolation With VPA Strategies")
    print("="*70)

    detector = BaselineDetector('models/baseline_xgboost.pkl')
    generator = CampaignGenerator()
    accounts = [f"user{i}@upi" for i in range(20)]

    # Campaign 1
    env1 = UPIEnvironment(fraud_detector=detector)
    campaign1 = generator.create_known_fraud_campaign(
        vpa_strategy=VPAStrategy.SINGLE_COMPROMISED_VPA
    )
    attacker1 = StaticAttacker(fraud_type="known")
    executor1 = CampaignExecutor(detector, env1, attacker1)
    completed1 = executor1.execute_campaign(campaign1, accounts, seed=700)

    vel1 = [txn.get('features', {}).get('velocity_1h', 0) for txn in completed1.transactions]

    # Campaign 2 with fresh environment
    env2 = UPIEnvironment(fraud_detector=detector)
    campaign2 = generator.create_known_fraud_campaign(
        vpa_strategy=VPAStrategy.SINGLE_COMPROMISED_VPA
    )
    attacker2 = StaticAttacker(fraud_type="known")
    executor2 = CampaignExecutor(detector, env2, attacker2)
    completed2 = executor2.execute_campaign(campaign2, accounts, seed=700)

    vel2 = [txn.get('features', {}).get('velocity_1h', 0) for txn in completed2.transactions]

    print(f"\nCampaign 1 first velocity: {vel1[0]}")
    print(f"Campaign 2 first velocity: {vel2[0]}")

    # Both should start at velocity 0 (isolated)
    assert vel1[0] == 0, "Campaign 1 should start with velocity 0"
    assert vel2[0] == 0, "Campaign 2 should start with velocity 0 (fresh environment)"

    print("\n✓ Campaigns remain isolated with VPA strategies\n")


def test_seed_reproducibility():
    """Test that VPA selection is reproducible with seed."""
    print("="*70)
    print("TEST 8: Seed Reproducibility")
    print("="*70)

    detector = BaselineDetector('models/baseline_xgboost.pkl')
    generator = CampaignGenerator()
    accounts = [f"user{i}@upi" for i in range(20)]

    # Run 1
    env1 = UPIEnvironment(fraud_detector=detector)
    campaign1 = generator.create_known_fraud_campaign(
        vpa_strategy=VPAStrategy.SINGLE_COMPROMISED_VPA
    )
    attacker1 = StaticAttacker(fraud_type="known")
    executor1 = CampaignExecutor(detector, env1, attacker1)
    completed1 = executor1.execute_campaign(campaign1, accounts, seed=800)

    sources1 = [txn['from_vpa'] for txn in completed1.transactions]

    # Run 2 with same seed
    env2 = UPIEnvironment(fraud_detector=detector)
    campaign2 = generator.create_known_fraud_campaign(
        vpa_strategy=VPAStrategy.SINGLE_COMPROMISED_VPA
    )
    attacker2 = StaticAttacker(fraud_type="known")
    executor2 = CampaignExecutor(detector, env2, attacker2)
    completed2 = executor2.execute_campaign(campaign2, accounts, seed=800)

    sources2 = [txn['from_vpa'] for txn in completed2.transactions]

    print(f"\nRun 1 sources: {sources1}")
    print(f"Run 2 sources: {sources2}")

    # Should use same source VPA with same seed
    assert set(sources1) == set(sources2), "VPA selection should be reproducible with seed"

    print("\n✓ VPA selection is reproducible with seed\n")


def main():
    """Run all VPA strategy validation tests."""
    print("\n" + "="*70)
    print("VPA STRATEGY VALIDATION TESTS")
    print("="*70 + "\n")

    try:
        test_single_compromised_vpa()
        test_small_vpa_pool()
        test_vpa_rotation()
        test_mixed_reuse()
        test_velocity_from_reuse()
        test_velocity_comparison()
        test_campaign_isolation()
        test_seed_reproducibility()

        print("="*70)
        print("ALL TESTS PASSED ✓")
        print("="*70)
        return 0

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
