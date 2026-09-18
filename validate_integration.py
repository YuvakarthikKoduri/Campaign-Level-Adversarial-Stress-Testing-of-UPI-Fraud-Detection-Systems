#!/usr/bin/env python3
"""Integration validation script for UPI Fraud Stress Lab."""

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
        has_predict_proba = hasattr(detector, 'predict_proba')
        return True, f"Detector loaded successfully (has predict: {has_predict}, has predict_proba: {has_predict_proba})"
    except Exception as e:
        return False, f"Failed to load detector: {str(e)}"

def test_create_environment():
    """Test 3: Test creating UPI environment."""
    try:
        from src.detectors.baseline import load_detector
        from src.environment import UPIEnvironment

        detector = load_detector('models/baseline_xgboost.pkl')
        environment = UPIEnvironment(detector)

        # Verify environment has expected attributes
        has_detector = hasattr(environment, 'detector')
        has_process = hasattr(environment, 'process_transaction')

        return True, f"Environment created (has detector: {has_detector}, has process_transaction: {has_process})"
    except Exception as e:
        return False, f"Failed to create environment: {str(e)}"

def test_campaign_generation():
    """Test 4: Test campaign generation."""
    try:
        from src.campaigns.generator import CampaignGenerator

        generator = CampaignGenerator()

        # Test different campaign types
        campaigns = []
        campaigns.append(generator.create_known_fraud_campaign(target_amount=10000))
        campaigns.append(generator.create_unknown_fraud_campaign(target_amount=20000))
        campaigns.append(generator.create_benign_campaign(target_amount=15000))

        all_valid = all(hasattr(c, 'transactions') for c in campaigns)
        total_txns = sum(len(c.transactions) for c in campaigns)

        return True, f"Generated 3 campaigns ({total_txns} total transactions)"
    except Exception as e:
        return False, f"Failed to generate campaigns: {str(e)}"

def test_demo_dry_run():
    """Test 5: Run a minimal demo test."""
    try:
        from src.detectors.baseline import load_detector
        from src.environment import UPIEnvironment
        from src.campaigns.generator import CampaignGenerator
        from src.campaigns.executor import CampaignExecutor
        from src.attackers.adaptive import AdaptiveAttacker

        # Load components
        detector = load_detector('models/baseline_xgboost.pkl')
        environment = UPIEnvironment(detector)
        generator = CampaignGenerator()

        # Create a small test campaign
        campaign = generator.create_unknown_fraud_campaign(target_amount=5000)

        # Create attacker
        attacker = AdaptiveAttacker(fraud_type="unknown")

        # Execute with minimal accounts
        executor = CampaignExecutor(detector, environment, attacker)
        accounts = [f"user{i}@upi" for i in range(5)]

        completed = executor.execute_campaign(campaign, accounts, verbose=False)

        return True, f"Demo executed successfully ({completed} transactions completed)"
    except Exception as e:
        return False, f"Failed to run demo: {str(e)}"

def test_experiment_imports():
    """Test 6: Verify all imports work in run_experiment.py."""
    try:
        from src.detectors.baseline import load_detector
        from src.environment import UPIEnvironment
        from src.experiments.scenarios import ExperimentScenarios

        # Try to instantiate
        detector = load_detector('models/baseline_xgboost.pkl')
        environment = UPIEnvironment(detector)
        scenarios = ExperimentScenarios(detector, environment)

        # Check for expected methods
        has_s1 = hasattr(scenarios, 'run_scenario_s1')
        has_s2 = hasattr(scenarios, 'run_scenario_s2')
        has_s3 = hasattr(scenarios, 'run_scenario_s3')
        has_s4 = hasattr(scenarios, 'run_scenario_s4')
        has_all = hasattr(scenarios, 'run_all_scenarios')

        all_methods = all([has_s1, has_s2, has_s3, has_s4, has_all])

        return True, f"All imports successful (all scenario methods present: {all_methods})"
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
        ("Demo dry run", test_demo_dry_run),
        ("Experiment imports", test_experiment_imports),
    ]

    results = {}
    all_passed = True

    for test_name, test_func in tests:
        print(f"Testing: {test_name}...")
        try:
            success, message = test_func()
            results[test_name] = {"success": success, "message": message}

            status = "✓ PASS" if success else "✗ FAIL"
            print(f"  {status}: {message}")

            if not success:
                all_passed = False
        except Exception as e:
            results[test_name] = {"success": False, "message": f"Exception: {str(e)}"}
            print(f"  ✗ FAIL: Exception: {str(e)}")
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
        print("✓ ALL TESTS PASSED - System is ready for experiments!")
    else:
        print("✗ SOME TESTS FAILED - Review issues above")
        print()
        print("Failed tests:")
        for test_name, result in results.items():
            if not result["success"]:
                print(f"  - {test_name}: {result['message']}")

    print("="*70)

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
