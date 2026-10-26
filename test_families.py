#!/usr/bin/env python3
"""
Test script for campaign families.

Demonstrates distinct behavioral mechanisms:
1. High-Value Burst (known fraud)
2. Slow Drain (unknown fraud)
3. Gradual Escalation (unseen mechanism)
4. Beneficiary Hopping (unseen mechanism)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.detectors.baseline import load_detector
from src.environment import UPIEnvironment
from src.campaigns.generator import CampaignGenerator, CampaignFamily
from src.campaigns.executor import CampaignExecutor
from src.attackers.static import StaticAttacker
from src.attackers.adaptive import AdaptiveAttacker
from src.attackers.family_based import GradualEscalationAttacker, BeneficiaryHoppingAttacker


def run_campaign_family(family_name: str, campaign, attacker, detector, environment, accounts):
    """Test a single campaign family."""
    print(f"\n{'='*70}")
    print(f"TESTING: {family_name}")
    print(f"Campaign: {campaign.campaign_id}")
    print(f"Family: {campaign.family.value if campaign.family else 'N/A'}")
    print(f"Target: ₹{campaign.target_amount:,.0f}")
    print(f"{'='*70}\n")

    executor = CampaignExecutor(detector, environment, attacker, max_steps=30)
    completed = executor.execute_campaign(campaign, accounts, verbose=False)

    print(f"\n{'-'*70}")
    print(f"RESULTS: {family_name}")
    print(f"{'-'*70}")
    print(f"Status: {completed.status.value}")
    print(f"Amount moved: ₹{completed.total_amount_moved:,.2f}")
    print(f"Amount blocked: ₹{completed.total_amount_blocked:,.2f}")
    print(f"Transactions: {len(completed.transactions)}")
    print(f"Success rate: {completed.total_amount_moved / completed.target_amount * 100:.1f}%")

    if hasattr(attacker, 'get_adaptation_summary'):
        summary = attacker.get_adaptation_summary()
        print(f"\nAttacker Behavior:")
        for key, val in summary.items():
            if isinstance(val, float):
                print(f"  {key}: {val:.2f}")
            else:
                print(f"  {key}: {val}")

    return completed


def main():
    print("="*70)
    print("UPI FRAUD STRESS LAB - CAMPAIGN FAMILY TESTING")
    print("="*70)

    # Load detector
    print("\nLoading trained detector...")
    detector = load_detector('models/baseline_xgboost.pkl')

    # Create environment
    environment = UPIEnvironment(fraud_detector=detector)

    # Generate test accounts
    accounts = [f"user{i}@upi" for i in range(30)]

    generator = CampaignGenerator()
    results = []

    # Test 1: High-Value Burst (Known)
    campaign1 = generator.create_known_fraud_campaign()
    attacker1 = StaticAttacker(fraud_type="known")
    result1 = run_campaign_family(
        "HIGH-VALUE BURST (Known/Static)",
        campaign1, attacker1, detector, environment, accounts
    )
    results.append(("High-Value Burst", result1))

    # Reset environment for next test
    environment.reset_statistics()

    # Test 2: Slow Drain (Unknown)
    campaign2 = generator.create_unknown_fraud_campaign()
    attacker2 = StaticAttacker(fraud_type="unknown")
    result2 = run_campaign_family(
        "SLOW DRAIN (Unknown/Static)",
        campaign2, attacker2, detector, environment, accounts
    )
    results.append(("Slow Drain", result2))

    environment.reset_statistics()

    # Test 3: Gradual Escalation
    campaign3 = generator.create_gradual_escalation_campaign()
    attacker3 = GradualEscalationAttacker(fraud_type="unknown")
    result3 = run_campaign_family(
        "GRADUAL ESCALATION (Unseen/Adaptive)",
        campaign3, attacker3, detector, environment, accounts
    )
    results.append(("Gradual Escalation", result3))

    environment.reset_statistics()

    # Test 4: Beneficiary Hopping
    campaign4 = generator.create_beneficiary_hopping_campaign()
    attacker4 = BeneficiaryHoppingAttacker(fraud_type="unknown")
    result4 = run_campaign_family(
        "BENEFICIARY HOPPING (Unseen/Adaptive)",
        campaign4, attacker4, detector, environment, accounts
    )
    results.append(("Beneficiary Hopping", result4))

    # Summary comparison
    print("\n" + "="*70)
    print("CAMPAIGN FAMILY COMPARISON")
    print("="*70)
    print(f"{'Family':<25} {'Status':<12} {'Amount Moved':<15} {'Success %':<10}")
    print("-"*70)

    for name, result in results:
        success_pct = result.total_amount_moved / result.target_amount * 100
        print(f"{name:<25} {result.status.value:<12} ₹{result.total_amount_moved:<13,.0f} {success_pct:<9.1f}%")

    print("="*70)
    print("\nKey Observations:")
    print("- Each family demonstrates DISTINCT behavioral mechanism")
    print("- These are single-campaign demonstrations, not estimated success rates")
    print("- Family mechanisms differ by construction; held-out generalization")
    print("  requires separate training/tuning provenance and evaluation")


if __name__ == "__main__":
    main()
