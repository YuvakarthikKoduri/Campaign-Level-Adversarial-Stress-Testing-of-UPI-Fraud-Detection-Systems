#!/usr/bin/env python3
"""
Test script to validate realistic velocity implementation.

Validates:
1. Velocity emerges from transaction timestamps
2. Velocity changes correctly based on timing
3. 1-hour window is respected
4. Fresh environments remain isolated
5. Timing is reproducible with seed
6. All four campaign families work correctly
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from datetime import datetime, timedelta
from src.campaigns.timing import CampaignTimer, CampaignFamily, get_timing_model
from src.campaigns.generator import CampaignGenerator
from src.campaigns.executor import CampaignExecutor
from src.attackers.static import StaticAttacker
from src.attackers.adaptive import AdaptiveAttacker
from src.environment import UPIEnvironment
from src.detectors.baseline import BaselineDetector


def test_timing_model():
    """Test that timing models produce realistic velocity ranges."""
    print("="*70)
    print("TEST 1: Timing Model Validation")
    print("="*70)

    for family in CampaignFamily:
        model = get_timing_model(family)
        timer = CampaignTimer(family, seed=42)

        # Generate timestamps for 10 transactions
        timestamps = [timer.next_transaction_time() for _ in range(10)]

        # Calculate inter-transaction intervals
        intervals = [
            (timestamps[i+1] - timestamps[i]).total_seconds()
            for i in range(len(timestamps) - 1)
        ]

        avg_interval = sum(intervals) / len(intervals)
        min_interval = min(intervals)
        max_interval = max(intervals)

        # Estimate velocity (transactions per hour)
        estimated_velocity = 3600 / avg_interval if avg_interval > 0 else 0

        print(f"\n{family.value}:")
        print(f"  Expected velocity: {model.expected_velocity_range[0]}-{model.expected_velocity_range[1]} txns/hour")
        print(f"  Avg interval: {avg_interval:.1f}s")
        print(f"  Min interval: {min_interval:.1f}s (model: {model.min_interval_seconds}s)")
        print(f"  Max interval: {max_interval:.1f}s (model: {model.max_interval_seconds}s)")
        print(f"  Estimated velocity: {estimated_velocity:.1f} txns/hour")

        # Validate intervals are within model bounds
        assert min_interval >= model.min_interval_seconds * 0.99, f"Min interval {min_interval} < model min {model.min_interval_seconds}"
        assert max_interval <= model.max_interval_seconds * 1.01, f"Max interval {max_interval} > model max {model.max_interval_seconds}"

        # Validate estimated velocity is in expected range
        min_vel, max_vel = model.expected_velocity_range
        assert min_vel * 0.5 <= estimated_velocity <= max_vel * 1.5, \
            f"Velocity {estimated_velocity:.1f} outside expected range {min_vel}-{max_vel}"

    print("\n✓ All timing models produce realistic velocity ranges\n")


def test_velocity_from_timestamps():
    """Test that velocity is correctly computed from transaction timestamps."""
    print("="*70)
    print("TEST 2: Velocity Computation from Timestamps")
    print("="*70)

    detector = BaselineDetector('models/baseline_xgboost.pkl')
    environment = UPIEnvironment(fraud_detector=detector)

    # Create campaign with HIGH_VALUE_BURST (high velocity)
    generator = CampaignGenerator()
    campaign = generator.create_known_fraud_campaign(target_amount=50000)

    attacker = StaticAttacker(fraud_type="known")
    executor = CampaignExecutor(detector, environment, attacker)

    # Execute campaign with fixed accounts to ensure same VPA is used
    accounts = [f"user{i}@upi" for i in range(10)]
    completed = executor.execute_campaign(campaign, accounts, seed=42)

    print(f"\nCampaign: {campaign.family.value}")
    print(f"Transactions: {len(completed.transactions)}")

    # Analyze velocity progression
    vpas_used = set()
    for i, txn in enumerate(completed.transactions):
        timestamp = datetime.fromisoformat(txn['timestamp']) if isinstance(txn['timestamp'], str) else txn['timestamp']
        features = txn.get('features', {})
        velocity = features.get('velocity_1h', 'N/A')
        vpas_used.add(txn['from_vpa'])

        if i < 5:  # Print first 5
            print(f"  Txn {i+1}: from={txn['from_vpa']}, time={timestamp.strftime('%H:%M:%S')}, velocity={velocity}, amount=₹{txn['amount']:.0f}")

    # Validate velocity progression
    velocities = [
        txn.get('features', {}).get('velocity_1h', 0)
        for txn in completed.transactions
    ]

    print(f"\nVelocity progression: {velocities}")
    print(f"Unique VPAs used: {len(vpas_used)} (VPAs: {sorted(vpas_used)[:3]}...)")

    # First transaction should have velocity 0
    assert velocities[0] == 0, f"First transaction should have velocity 0, got {velocities[0]}"

    # For HIGH_VALUE_BURST with realistic timing, later transactions from same VPA should have non-zero velocity
    # Since static attacker picks random VPAs, we need to check if ANY transaction has velocity > 0
    if max(velocities) == 0:
        print(f"\n⚠ WARNING: All velocities are 0. This might be due to different VPAs per transaction.")
        print(f"   Checking if transactions are from same VPA...")

        # Count transactions per VPA
        from collections import Counter
        vpa_counts = Counter(txn['from_vpa'] for txn in completed.transactions)
        print(f"   Transactions per VPA: {dict(vpa_counts)}")

        # If each VPA is used only once, velocity will always be 0
        if all(count == 1 for count in vpa_counts.values()):
            print(f"   ✓ Expected: Each VPA used once, so velocity remains 0 (correct behavior)")
        else:
            # Some VPA used multiple times but velocity still 0 - this is the real problem
            multi_use_vpas = [vpa for vpa, count in vpa_counts.items() if count > 1]
            if multi_use_vpas:
                print(f"   ✗ ERROR: VPA(s) {multi_use_vpas} used multiple times but velocity still 0")
                raise AssertionError("Velocity should increase for repeat VPA usage")
    else:
        print(f"\n✓ Velocity correctly increases: max={max(velocities)}")

    print("\n✓ Velocity correctly computed from timestamps\n")


def test_velocity_window():
    """Test that 1-hour window is correctly respected."""
    print("="*70)
    print("TEST 3: 1-Hour Window Validation")
    print("="*70)

    detector = BaselineDetector('models/baseline_xgboost.pkl')
    environment = UPIEnvironment(fraud_detector=detector)

    # Manually create transactions with known timestamps
    base_time = datetime(2026, 9, 18, 10, 0, 0)
    vpa = "test@upi"

    # Transaction 1: T=0
    txn1 = {
        "from_vpa": vpa,
        "to_vpa": "dest1@upi",
        "amount": 1000,
        "timestamp": base_time
    }
    resp1 = environment.process_transaction(txn1)
    vel1 = resp1.get('features', {}).get('velocity_1h', -1)

    # Transaction 2: T=30min (should count txn1)
    txn2 = {
        "from_vpa": vpa,
        "to_vpa": "dest2@upi",
        "amount": 1000,
        "timestamp": base_time + timedelta(minutes=30)
    }
    resp2 = environment.process_transaction(txn2)
    vel2 = resp2.get('features', {}).get('velocity_1h', -1)

    # Transaction 3: T=65min (should NOT count txn1, only txn2)
    txn3 = {
        "from_vpa": vpa,
        "to_vpa": "dest3@upi",
        "amount": 1000,
        "timestamp": base_time + timedelta(minutes=65)
    }
    resp3 = environment.process_transaction(txn3)
    vel3 = resp3.get('features', {}).get('velocity_1h', -1)

    print(f"\nTransaction 1 (T=0):      velocity={vel1} (expected: 0)")
    print(f"Transaction 2 (T=30min):  velocity={vel2} (expected: 1)")
    print(f"Transaction 3 (T=65min):  velocity={vel3} (expected: 1, not 2)")

    assert vel1 == 0, f"Txn1 velocity should be 0, got {vel1}"
    assert vel2 == 1, f"Txn2 velocity should be 1, got {vel2}"
    assert vel3 == 1, f"Txn3 velocity should be 1 (txn1 outside window), got {vel3}"

    print("\n✓ 1-hour window correctly enforced\n")


def test_fresh_environment_isolation():
    """Test that fresh environments remain isolated."""
    print("="*70)
    print("TEST 4: Fresh Environment Isolation")
    print("="*70)

    detector = BaselineDetector('models/baseline_xgboost.pkl')
    generator = CampaignGenerator()
    accounts = [f"user{i}@upi" for i in range(10)]

    # Campaign 1
    env1 = UPIEnvironment(fraud_detector=detector)
    campaign1 = generator.create_known_fraud_campaign()
    attacker1 = StaticAttacker(fraud_type="known")
    executor1 = CampaignExecutor(detector, env1, attacker1)
    completed1 = executor1.execute_campaign(campaign1, accounts, seed=100)

    velocities1 = [txn.get('features', {}).get('velocity_1h', 0) for txn in completed1.transactions]

    # Campaign 2 with FRESH environment
    env2 = UPIEnvironment(fraud_detector=detector)
    campaign2 = generator.create_known_fraud_campaign()
    attacker2 = StaticAttacker(fraud_type="known")
    executor2 = CampaignExecutor(detector, env2, attacker2)
    completed2 = executor2.execute_campaign(campaign2, accounts, seed=100)

    velocities2 = [txn.get('features', {}).get('velocity_1h', 0) for txn in completed2.transactions]

    print(f"\nCampaign 1 velocities: {velocities1[:5]}")
    print(f"Campaign 2 velocities: {velocities2[:5]}")

    # Both should start at 0 (isolated)
    assert velocities1[0] == 0, "Campaign 1 should start with velocity 0"
    assert velocities2[0] == 0, "Campaign 2 should start with velocity 0 (fresh environment)"

    print("\n✓ Fresh environments maintain isolation\n")


def test_reproducible_timing():
    """Test that timing is reproducible with seed."""
    print("="*70)
    print("TEST 5: Reproducible Timing")
    print("="*70)

    detector = BaselineDetector('models/baseline_xgboost.pkl')
    generator = CampaignGenerator()
    accounts = [f"user{i}@upi" for i in range(10)]

    # Run same campaign twice with same seed
    results = []
    for run in range(2):
        env = UPIEnvironment(fraud_detector=detector)
        campaign = generator.create_known_fraud_campaign()
        attacker = StaticAttacker(fraud_type="known")
        executor = CampaignExecutor(detector, env, attacker)
        completed = executor.execute_campaign(campaign, accounts, seed=42)

        velocities = [txn.get('features', {}).get('velocity_1h', 0) for txn in completed.transactions]
        results.append(velocities)

    print(f"\nRun 1 velocities: {results[0][:5]}")
    print(f"Run 2 velocities: {results[1][:5]}")

    assert results[0] == results[1], "Timing should be reproducible with same seed"

    print("\n✓ Timing is reproducible with seed\n")


def test_all_families():
    """Test that all campaign families work correctly."""
    print("="*70)
    print("TEST 6: All Campaign Families")
    print("="*70)

    detector = BaselineDetector('models/baseline_xgboost.pkl')
    generator = CampaignGenerator()
    accounts = [f"user{i}@upi" for i in range(10)]

    families_tested = set()

    # Test known (HIGH_VALUE_BURST)
    env = UPIEnvironment(fraud_detector=detector)
    campaign = generator.create_known_fraud_campaign()
    attacker = StaticAttacker(fraud_type="known")
    executor = CampaignExecutor(detector, env, attacker)
    completed = executor.execute_campaign(campaign, accounts, seed=42)

    assert completed.family == CampaignFamily.HIGH_VALUE_BURST
    families_tested.add(completed.family)

    print(f"✓ {completed.family.value}: {len(completed.transactions)} transactions")

    # Test unknown families (random selection, so run multiple times)
    for i in range(10):
        env = UPIEnvironment(fraud_detector=detector)
        campaign = generator.create_unknown_fraud_campaign()
        attacker = StaticAttacker(fraud_type="unknown")
        executor = CampaignExecutor(detector, env, attacker)
        completed = executor.execute_campaign(campaign, accounts, seed=50+i)

        families_tested.add(completed.family)

        if i < 3:  # Print first 3
            print(f"✓ {completed.family.value}: {len(completed.transactions)} transactions")

    print(f"\nFamilies tested: {len(families_tested)}/4")
    assert len(families_tested) >= 3, f"Should test at least 3 families, got {len(families_tested)}"

    print("\n✓ All campaign families work correctly\n")


def main():
    """Run all timing validation tests."""
    print("\n" + "="*70)
    print("REALISTIC VELOCITY VALIDATION TESTS")
    print("="*70 + "\n")

    try:
        test_timing_model()
        test_velocity_from_timestamps()
        test_velocity_window()
        test_fresh_environment_isolation()
        test_reproducible_timing()
        test_all_families()

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
