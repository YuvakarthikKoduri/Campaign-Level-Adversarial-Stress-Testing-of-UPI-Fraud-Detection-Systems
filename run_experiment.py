#!/usr/bin/env python3
"""Experiment runner for S1-S4 scenarios."""

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
    args = parser.parse_args()

    print("="*60)
    print("UPI FRAUD STRESS LAB - EXPERIMENT RUNNER")
    print("="*60)
    print()

    # Load detector
    print("Loading trained detector...")
    detector = load_detector('models/baseline_xgboost.pkl')
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
        results = scenarios.run_all_scenarios(args.campaigns)

        # Print results for all scenarios
        print("\n" + "="*60)
        print("RESULTS SUMMARY")
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

        # Print results
        print(f"\n{args.scenario} Results:")
        print("-"*40)
        for k, v in results.items():
            if isinstance(v, float):
                print(f"  {k}: {v:.4f}")
            else:
                print(f"  {k}: {v}")

    print("\n" + "="*60)
    print("Experiment complete!")
    print("="*60)

if __name__ == "__main__":
    main()
