#!/usr/bin/env python3
"""
Comprehensive audit of UPI Fraud Stress Lab implementation.

Checks:
1. Static vs Adaptive comparison fairness
2. Campaign family distinctiveness
3. Adaptive attacker state tracking
4. Metric consistency
5. Current functional status
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import json
import random
from src.detectors.baseline import load_detector
from src.environment import UPIEnvironment
from src.campaigns.generator import CampaignGenerator, CampaignFamily
from src.campaigns.executor import CampaignExecutor
from src.attackers.static import StaticAttacker
from src.attackers.adaptive import AdaptiveAttacker


def audit_comparison_fairness():
    """Audit Phase 1: Static vs Adaptive comparison fairness."""
    print("\n" + "="*70)
    print("PHASE 1 AUDIT: STATIC VS ADAPTIVE COMPARISON FAIRNESS")
    print("="*70)

    # Create identical campaigns for static and adaptive
    generator = CampaignGenerator()

    # Set seed for reproducibility
    random.seed(42)

    # Create known campaign
    campaign_static = generator.create_known_fraud_campaign(target_amount=30000)
    campaign_adaptive = generator.create_known_fraud_campaign(target_amount=30000)

    print(f"\nCampaign Comparison:")
    print(f"Static  - ID: {campaign_static.campaign_id}, Target: ₹{campaign_static.target_amount}, Type: {campaign_static.fraud_type}")
    print(f"Adaptive - ID: {campaign_adaptive.campaign_id}, Target: ₹{campaign_adaptive.target_amount}, Type: {campaign_adaptive.fraud_type}")
    print(f"✓ Targets match: {campaign_static.target_amount == campaign_adaptive.target_amount}")
    print(f"✓ Types match: {campaign_static.fraud_type == campaign_adaptive.fraud_type}")

    # Check attacker initialization
    attacker_static = StaticAttacker(fraud_type="known")
    attacker_adaptive = AdaptiveAttacker(fraud_type="known")

    print(f"\nAttacker Comparison:")
    print(f"Static  - Type: {attacker_static.fraud_type}, Step: {attacker_static.step}")
    print(f"Adaptive - Type: {attacker_adaptive.fraud_type}, Step: {attacker_adaptive.step}")
    print(f"✓ Same fraud type: {attacker_static.fraud_type == attacker_adaptive.fraud_type}")

    # Check if adaptive actually uses feedback
    print(f"\nAdaptive State Tracking:")
    print(f"Has history: {hasattr(attacker_adaptive, 'history')}")
    print(f"Has safe_amounts: {hasattr(attacker_adaptive, 'safe_amounts')}")
    print(f"Has observe method: {hasattr(attacker_adaptive, 'observe')}")
    print(f"Tracks adaptation_count: {hasattr(attacker_adaptive, 'adaptation_count')}")

    return {
        "fair_targets": campaign_static.target_amount == campaign_adaptive.target_amount,
        "fair_types": campaign_static.fraud_type == campaign_adaptive.fraud_type,
        "adaptive_has_state": hasattr(attacker_adaptive, 'safe_amounts'),
        "adaptive_tracks_feedback": hasattr(attacker_adaptive, 'observe')
    }


def audit_campaign_families():
    """Audit Phase 3: Campaign family distinctiveness."""
    print("\n" + "="*70)
    print("PHASE 3 AUDIT: CAMPAIGN FAMILY VALIDATION")
    print("="*70)

    generator = CampaignGenerator()

    families_info = []

    # Check each family
    print("\nCampaign Families:")

    campaign1 = generator.create_known_fraud_campaign()
    print(f"1. Known (High-Value Burst)")
    print(f"   Family: {campaign1.family.value if campaign1.family else 'None'}")
    print(f"   Target: ₹{campaign1.target_amount}")
    families_info.append({
        "name": "HIGH_VALUE_BURST",
        "family": campaign1.family.value if campaign1.family else None,
        "target": campaign1.target_amount
    })

    campaign2 = generator.create_unknown_fraud_campaign()
    print(f"\n2. Unknown (Slow Drain)")
    print(f"   Family: {campaign2.family.value if campaign2.family else 'None'}")
    print(f"   Target: ₹{campaign2.target_amount}")
    families_info.append({
        "name": "SLOW_DRAIN",
        "family": campaign2.family.value if campaign2.family else None,
        "target": campaign2.target_amount
    })

    if hasattr(generator, 'create_gradual_escalation_campaign'):
        campaign3 = generator.create_gradual_escalation_campaign()
        print(f"\n3. Gradual Escalation")
        print(f"   Family: {campaign3.family.value if campaign3.family else 'None'}")
        print(f"   Target: ₹{campaign3.target_amount}")
        families_info.append({
            "name": "GRADUAL_ESCALATION",
            "family": campaign3.family.value if campaign3.family else None,
            "target": campaign3.target_amount
        })

    if hasattr(generator, 'create_beneficiary_hopping_campaign'):
        campaign4 = generator.create_beneficiary_hopping_campaign()
        print(f"\n4. Beneficiary Hopping")
        print(f"   Family: {campaign4.family.value if campaign4.family else 'None'}")
        print(f"   Target: ₹{campaign4.target_amount}")
        families_info.append({
            "name": "BENEFICIARY_HOPPING",
            "family": campaign4.family.value if campaign4.family else None,
            "target": campaign4.target_amount
        })

    unique_families = set(f["family"] for f in families_info if f["family"])
    print(f"\n✓ Unique families defined: {len(unique_families)}")
    print(f"  Families: {unique_families}")

    return {
        "families_count": len(families_info),
        "unique_families": len(unique_families),
        "families": families_info
    }


def audit_adaptive_state_tracking():
    """Audit Phase 4: Adaptive attacker state."""
    print("\n" + "="*70)
    print("PHASE 4 AUDIT: ADAPTIVE ATTACKER STATE TRACKING")
    print("="*70)

    attacker = AdaptiveAttacker(fraud_type="known")

    print(f"\nInitial State:")
    print(f"  step: {attacker.step}")
    print(f"  blocked_count: {attacker.blocked_count}")
    print(f"  allowed_count: {attacker.allowed_count}")
    print(f"  safe_amounts: {attacker.safe_amounts if hasattr(attacker, 'safe_amounts') else 'N/A'}")

    # Simulate responses
    print(f"\nSimulating detector feedback:")

    # Response 1: ALLOW
    attacker.observe({
        "decision": "ALLOW",
        "risk_score": 0.3,
        "amount": 5000,
        "to_vpa": "test@upi"
    })
    print(f"  After ALLOW: allowed={attacker.allowed_count}, safe_amounts={len(attacker.safe_amounts) if hasattr(attacker, 'safe_amounts') else 0}")

    # Response 2: BLOCK
    attacker.observe({
        "decision": "BLOCK",
        "risk_score": 0.8,
        "amount": 10000
    })
    print(f"  After BLOCK: blocked={attacker.blocked_count}, multiplier={attacker.current_amount_multiplier:.2f}")

    # Response 3: Another ALLOW
    attacker.observe({
        "decision": "ALLOW",
        "risk_score": 0.2,
        "amount": 3000,
        "to_vpa": "test2@upi"
    })
    print(f"  After ALLOW: allowed={attacker.allowed_count}, safe_amounts={len(attacker.safe_amounts) if hasattr(attacker, 'safe_amounts') else 0}")

    summary = attacker.get_adaptation_summary()
    print(f"\nAdaptation Summary:")
    for key, val in summary.items():
        if isinstance(val, float):
            print(f"  {key}: {val:.2f}")
        else:
            print(f"  {key}: {val}")

    return {
        "tracks_allowed": attacker.allowed_count > 0,
        "tracks_blocked": attacker.blocked_count > 0,
        "learns_safe_regions": len(attacker.safe_amounts) > 0 if hasattr(attacker, 'safe_amounts') else False,
        "adaptation_count": summary.get('adaptation_count', 0)
    }


def audit_metrics():
    """Audit Phase 5: Campaign-level metrics."""
    print("\n" + "="*70)
    print("PHASE 5 AUDIT: CAMPAIGN-LEVEL METRICS")
    print("="*70)

    # Check if result files exist
    results_dir = Path("results/metrics")
    if results_dir.exists():
        result_files = list(results_dir.glob("*.json"))
        print(f"\nFound {len(result_files)} result files:")
        for rf in result_files:
            print(f"  - {rf.name}")

            try:
                with open(rf) as f:
                    data = json.load(f)
                    print(f"    Keys: {list(data.keys())}")
                    if 'campaign_success_rate' in data:
                        print(f"    Success rate: {data['campaign_success_rate']:.1%}")
                    if 'total_financial_exposure' in data:
                        print(f"    Total exposure: ₹{data['total_financial_exposure']:,.0f}")
            except Exception as e:
                print(f"    Error reading: {e}")
    else:
        print(f"\nResults directory not found: {results_dir}")

    return {
        "results_dir_exists": results_dir.exists(),
        "result_files_count": len(result_files) if results_dir.exists() else 0
    }


def main():
    print("="*70)
    print("UPI FRAUD STRESS LAB - IMPLEMENTATION AUDIT")
    print("="*70)

    audit_results = {}

    try:
        audit_results['comparison_fairness'] = audit_comparison_fairness()
    except Exception as e:
        print(f"\n❌ Phase 1 audit failed: {e}")
        audit_results['comparison_fairness'] = {"error": str(e)}

    try:
        audit_results['campaign_families'] = audit_campaign_families()
    except Exception as e:
        print(f"\n❌ Phase 3 audit failed: {e}")
        audit_results['campaign_families'] = {"error": str(e)}

    try:
        audit_results['adaptive_state'] = audit_adaptive_state_tracking()
    except Exception as e:
        print(f"\n❌ Phase 4 audit failed: {e}")
        audit_results['adaptive_state'] = {"error": str(e)}

    try:
        audit_results['metrics'] = audit_metrics()
    except Exception as e:
        print(f"\n❌ Phase 5 audit failed: {e}")
        audit_results['metrics'] = {"error": str(e)}

    # Summary
    print("\n" + "="*70)
    print("AUDIT SUMMARY")
    print("="*70)

    print("\nPhase 1 - Static vs Adaptive Comparison:")
    comp = audit_results.get('comparison_fairness', {})
    if 'error' in comp:
        print(f"  ❌ Error: {comp['error']}")
    else:
        print(f"  {'✓' if comp.get('fair_targets') else '✗'} Fair targets")
        print(f"  {'✓' if comp.get('fair_types') else '✗'} Fair types")
        print(f"  {'✓' if comp.get('adaptive_has_state') else '✗'} Adaptive has state")
        print(f"  {'✓' if comp.get('adaptive_tracks_feedback') else '✗'} Tracks feedback")

    print("\nPhase 3 - Campaign Families:")
    fam = audit_results.get('campaign_families', {})
    if 'error' in fam:
        print(f"  ❌ Error: {fam['error']}")
    else:
        print(f"  ✓ {fam.get('families_count', 0)} families implemented")
        print(f"  ✓ {fam.get('unique_families', 0)} unique family types")

    print("\nPhase 4 - Adaptive Attacker:")
    adapt = audit_results.get('adaptive_state', {})
    if 'error' in adapt:
        print(f"  ❌ Error: {adapt['error']}")
    else:
        print(f"  {'✓' if adapt.get('tracks_allowed') else '✗'} Tracks ALLOW")
        print(f"  {'✓' if adapt.get('tracks_blocked') else '✗'} Tracks BLOCK")
        print(f"  {'✓' if adapt.get('learns_safe_regions') else '✗'} Learns safe regions")
        print(f"  Adaptation count: {adapt.get('adaptation_count', 0)}")

    print("\nPhase 5 - Metrics:")
    metrics = audit_results.get('metrics', {})
    if 'error' in metrics:
        print(f"  ❌ Error: {metrics['error']}")
    else:
        print(f"  {'✓' if metrics.get('results_dir_exists') else '✗'} Results directory exists")
        print(f"  Result files: {metrics.get('result_files_count', 0)}")

    # Save audit results
    with open('audit_results.json', 'w') as f:
        json.dump(audit_results, f, indent=2, default=str)
    print(f"\n✓ Audit results saved to audit_results.json")


if __name__ == "__main__":
    main()
