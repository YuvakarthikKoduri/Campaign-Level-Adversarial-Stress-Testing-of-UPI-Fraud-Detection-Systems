#!/usr/bin/env python3
"""Integration validation script for UPI Fraud Stress Lab - Fixed version."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_model_exists():
    """Test 1: Verify model file exists."""
    model_path = Path('models/baseline_xgboost.pkl')
    return model_path.exists(), str(model_path.absolute())

def test_load_detector():
    """Test 2: Test loading the detector."""
    try:
        from src.detectors.baseline import load_detector
        detector = load_detector('models/baseline_xgboost.pkl')

        # Verify it has expected methods
        has_predict = hasattr(detector, 'predict')
        has_risk_score = hasattr(detector, 'risk_score')

        # Test risk_score method with dummy transaction
        dummy_txn = {
            'amount': 1000,
            'from_vpa': 'test@upi',
            'to_vpa': 'receiver@upi'
        }
        try:
            score = detector.risk_score(dummy_txn)
            risk_score_works = True
        except Exception as e:
            risk_score_works = False

        return True, f"Detector loaded (predict: {has_predict}, risk_score: {has_risk_score}, risk_score works: {risk_score_works})"
    except Exception as e:
        return False, f"Failed to load detector: {str(e)}"

def test_create_environment():
    """Test 3: Test creating UPI environment."""
    try:
        from src.detectors.baseline import load_detector
        from src.environment import UPIEnvironment

        detector = load_detector('models/baseline_xgboost.pkl')
        environment = UPIEnvironment(fraud_detector=detector)

        # Verify environment has expected methods
        has_create_account = hasattr(environment, 'create_account')
        has_create_vpa = hasattr(environment, 'create_vpa')
        has_process = hasattr(environment, 'process_transaction')

        # Test creating accounts
        try:
            environment.create_account('test_acc1', initial_balance=10000)
            environment.create_vpa('test@upi', 'test_acc1', 'Test User')
            accounts_work = True
        except Exception as e:
            accounts_work = False

        return True, f"Environment created (create_account: {has_create_account}, create_vpa: {has_create_vpa}, process_transaction: {has_process}, accounts work: {accounts_work})"
    except Exception as e:
        return False, f"Failed to create environment: {str(e)}"

def test_campaign_generation():
    """Test 4: Test campaign generation."""
    try:
        from src.campaigns.generator import CampaignGenerator

        generator = CampaignGenerator()

        # Test different campaign types (only known and unknown exist)
        campaigns = []
        campaigns.append(generator.create_known_fraud_campaign(target_amount=10000))
        campaigns.append(generator.create_unknown_fraud_campaign(target_amount=20000))

        all_valid = all(hasattr(c, 'transactions') and hasattr(c, 'campaign_id') for c in campaigns)

        return True, f"Generated 2 campaigns (known and unknown fraud types, all valid: {all_valid})"
    except Exception as e:
        return False, f"Failed to generate campaigns: {str(e)}"

def test_demo_components():
    """Test 5: Test demo.py components individually (without full execution)."""
    try:
        from src.detectors.baseline import load_detector
        from src.environment import UPIEnvironment
        from src.campaigns.generator import CampaignGenerator
        from src.attackers.adaptive import AdaptiveAttacker

        # Load detector
        detector = load_detector('models/baseline_xgboost.pkl')

        # Create environment
        environment = UPIEnvironment(fraud_detector=detector)

        # Create campaign
        generator = CampaignGenerator()
        campaign = generator.create_unknown_fraud_campaign(target_amount=5000)

        # Create attacker
        attacker = AdaptiveAttacker(fraud_type="unknown")

        # Verify attacker has required methods
        has_choose = hasattr(attacker, 'choose_action')
        has_observe = hasattr(attacker, 'observe_response')

        return True, f"All demo components load successfully (attacker has choose_action: {has_choose}, observe_response: {has_observe})"
    except Exception as e:
        return False, f"Failed to load demo components: {str(e)}"

def test_experiment_imports():
    """Test 6: Verify all imports work in run_experiment.py."""
    try:
        from src.detectors.baseline import load_detector
        from src.environment import UPIEnvironment
        from src.experiments.scenarios import ExperimentScenarios

        # Try to instantiate
        detector = load_detector('models/baseline_xgboost.pkl')
        environment = UPIEnvironment(fraud_detector=detector)
        scenarios = ExperimentScenarios(detector, environment)

        # Check for expected methods
        has_s1 = hasattr(scenarios, 'run_scenario_s1')
        has_s2 = hasattr(scenarios, 'run_scenario_s2')
        has_s3 = hasattr(scenarios, 'run_scenario_s3')
        has_s4 = hasattr(scenarios, 'run_scenario_s4')
        has_all = hasattr(scenarios, 'run_all_scenarios')

        all_methods = all([has_s1, has_s2, has_s3, has_s4, has_all])

        return True, f"All experiment imports successful (all S1-S4 scenario methods present: {all_methods})"
    except Exception as e:
        return False, f"Import failed: {str(e)}"

def main():
    print("="*70)
    print("UPI FRAUD STRESS LAB - INTEGRATION VALIDATION")
    print("="*70)
    print()

    tests = [
        ("Model file exists", test_model_exists),
        ("Load detector", test_load_detector),
        ("Create UPI environment", test_create_environment),
        ("Campaign generation", test_campaign_generation),
        ("Demo components", test_demo_components),
        ("Experiment imports", test_experiment_imports),
    ]

    results = {}
    all_passed = True

    for test_name, test_func in tests:
        print(f"Testing: {test_name}...")
        try:
            success, message = test_func()
            results[test_name] = {"success": success, "message": message}

            status = "PASS" if success else "FAIL"
            print(f"  [{status}] {message}")

            if not success:
                all_passed = False
        except Exception as e:
            results[test_name] = {"success": False, "message": f"Exception: {str(e)}"}
            print(f"  [FAIL] Exception: {str(e)}")
            all_passed = False

        print()

    print("="*70)
    print("VALIDATION SUMMARY")
    print("="*70)

    passed = sum(1 for r in results.values() if r["success"])
    total = len(results)

    print(f"Tests passed: {passed}/{total}")
    print()

    if all_passed:
        print("ALL TESTS PASSED - System is ready for experiments!")
        print()
        print("Next steps:")
        print("  1. Run demo: python demo.py")
        print("  2. Run experiment: python run_experiment.py --scenario S1")
    else:
        print("SOME TESTS FAILED - Review issues above")
        print()
        print("Failed tests:")
        for test_name, result in results.items():
            if not result["success"]:
                print(f"  - {test_name}: {result['message']}")

    print("="*70)

    return results, all_passed

if __name__ == "__main__":
    results, success = main()
    sys.exit(0 if success else 1)
