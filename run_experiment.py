#!/usr/bin/env python3
"""Experiment runner for S1-S4 scenarios with multi-detector support."""

import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.detectors.baseline import load_detector
from src.environment import UPIEnvironment
from src.experiments.scenarios import ExperimentScenarios

def main():
    parser = argparse.ArgumentParser(
        description='Run UPI Fraud Stress Lab experiments',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_experiment.py --scenario S1
  python run_experiment.py --scenario S4 --campaigns 200
  python run_experiment.py --scenario all
  python run_experiment.py --scenario all --detector random_forest
  python run_experiment.py --scenario all --detector both
        """
    )
    parser.add_argument(
        '--scenario',
        choices=['S1', 'S2', 'S3', 'S4', 'all'],
        default='S1',
        help='Scenario to run (S1, S2, S3, S4, or all)'
    )
    parser.add_argument(
        '--campaigns',
        type=int,
        default=100,
        help='Number of campaigns to run (default: 100)'
    )
    parser.add_argument(
        '--detector',
        choices=['xgboost', 'random_forest', 'both'],
        default='xgboost',
        help='Detector to use (default: xgboost)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=None,
        help='Random seed for reproducibility (optional)'
    )
    args = parser.parse_args()

    print("="*60)
    print("UPI FRAUD STRESS LAB - EXPERIMENT RUNNER")
    print("="*60)
    print()

    # Set random seed if provided
    if args.seed is not None:
        import random
        import numpy as np
        random.seed(args.seed)
        np.random.seed(args.seed)
        print(f"Random seed set to: {args.seed}")
        print()

    # Determine which detectors to run
    detectors_to_run = []
    if args.detector in ['xgboost', 'both']:
        detectors_to_run.append(('XGBoost', 'models/baseline_xgboost.pkl'))
    if args.detector in ['random_forest', 'both']:
        detectors_to_run.append(('Random Forest', 'models/baseline_random_forest.pkl'))

    # Run experiments for each detector
    all_results = {}

    for detector_name, model_path in detectors_to_run:
        print(f"\n{'='*60}")
        print(f"DETECTOR: {detector_name}")
        print(f"{'='*60}")

        # Load detector
        print(f"Loading {detector_name} detector...")
        detector = load_detector(model_path)
        print("Detector loaded successfully")
        print()

        # Create environment
        environment = UPIEnvironment(fraud_detector=detector)

        # Create scenarios object
        scenarios = ExperimentScenarios(detector, environment)

        # Run selected scenario(s)
        if args.scenario == 'all':
            print(f"Running ALL scenarios with {args.campaigns} campaigns each...")
            print()
            results = scenarios.run_all_scenarios(args.campaigns, save_results=True, detector_name=detector_name)

            # Store results
            all_results[detector_name] = results

            # Print results for all scenarios
            print("\n" + "="*60)
            print(f"{detector_name} - RESULTS SUMMARY")
            print("="*60)
            for scenario_name, scenario_results in results.items():
                print(f"\n{scenario_name}:")
                for k, v in scenario_results.items():
                    if isinstance(v, float):
                        print(f"  {k}: {v:.4f}")
                    else:
                        print(f"  {k}: {v}")
        else:
            print(f"Running scenario {args.scenario} with {args.campaigns} campaigns...")
            print()

            # Get the appropriate method
            method = getattr(scenarios, f'run_scenario_{args.scenario.lower()}')
            results = method(args.campaigns, verbose=True)

            # Store results
            all_results[detector_name] = {args.scenario: results}

            # Print results
            print(f"\n{detector_name} - {args.scenario} Results:")
            print("-"*40)
            for k, v in results.items():
                if isinstance(v, float):
                    print(f"  {k}: {v:.4f}")
                else:
                    print(f"  {k}: {v}")

    # Print comparison if multiple detectors
    if len(detectors_to_run) > 1 and args.scenario == 'all':
        print("\n" + "="*60)
        print("DETECTOR COMPARISON")
        print("="*60)

        scenarios_list = ['S1', 'S2', 'S3', 'S4']
        print(f"\n{'Scenario':<12} {'Metric':<25} {'XGBoost':<15} {'Random Forest':<15} {'Difference'}")
        print("-"*80)

        for scenario in scenarios_list:
            xgb_success = all_results['XGBoost'][scenario]['campaign_success_rate']
            rf_success = all_results['Random Forest'][scenario]['campaign_success_rate']
            print(f"{scenario:<12} {'Success Rate':<25} {xgb_success:>14.1%} {rf_success:>14.1%}  {xgb_success - rf_success:+.3f}")

            xgb_exposure = all_results['XGBoost'][scenario]['total_financial_exposure']
            rf_exposure = all_results['Random Forest'][scenario]['total_financial_exposure']
            print(f"{'':12} {'Total Exposure':<25} ₹{xgb_exposure:>12,.0f} ₹{rf_exposure:>12,.0f}  ₹{xgb_exposure - rf_exposure:+,.0f}")
            print()

    print("\n" + "="*60)
    print("Experiment complete!")
    print("="*60)

if __name__ == "__main__":
    main()
