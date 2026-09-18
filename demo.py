#!/usr/bin/env python3
"""Live demonstration of adaptive attacker."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.detectors.baseline import load_detector
from src.environment import UPIEnvironment
from src.campaigns.generator import CampaignGenerator
from src.campaigns.executor import CampaignExecutor
from src.attackers.adaptive import AdaptiveAttacker

def main():
    print("="*60)
    print("UPI FRAUD STRESS LAB - LIVE DEMO")
    print("="*60)
    print()

    # Load detector
    print("Loading trained detector...")
    detector = load_detector('models/baseline_xgboost.pkl')

    # Create environment
    environment = UPIEnvironment(fraud_detector=detector)

    # Create unknown fraud campaign (using default feasible target)
    generator = CampaignGenerator()
    campaign = generator.create_unknown_fraud_campaign()

    # Create adaptive attacker
    attacker = AdaptiveAttacker(fraud_type="unknown")

    # Execute campaign
    executor = CampaignExecutor(detector, environment, attacker)
    accounts = [f"user{i}@upi" for i in range(20)]

    print("Executing campaign with adaptive attacker...")
    print()

    completed = executor.execute_campaign(campaign, accounts, verbose=True)

    # Show adaptation summary
    if hasattr(attacker, 'get_adaptation_summary'):
        summary = attacker.get_adaptation_summary()
        print("\nAdaptive Behavior Summary:")
        print(f"  Total steps: {summary['steps']}")
        print(f"  Blocked: {summary['blocked_count']}")
        print(f"  Flagged: {summary['flagged_count']}")
        print(f"  Allowed: {summary['allowed_count']}")
        print(f"  Final amount multiplier: {summary['amount_multiplier']:.2f}x")
        print(f"  Unique beneficiaries used: {summary['unique_beneficiaries']}")

if __name__ == "__main__":
    main()
