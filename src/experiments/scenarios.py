"""
Experiment scenarios S1-S4.
"""
from typing import List, Dict
import json
from pathlib import Path

from src.campaigns.generator import CampaignGenerator
from src.campaigns.executor import CampaignExecutor
from src.attackers.static import StaticAttacker
from src.attackers.adaptive import AdaptiveAttacker
from src.evaluation.metrics import CampaignMetrics


class ExperimentScenarios:
    """
    Four experimental scenarios:

    S1: Known Fraud + Static Attacker
    S2: Known Fraud + Adaptive Attacker
    S3: Unknown Fraud + Static Attacker
    S4: Unknown Fraud + Adaptive Attacker (PRIMARY STRESS TEST)
    """

    def __init__(self, detector, environment):
        """
        Initialize experiment scenarios.

        Args:
            detector: Trained fraud detector
            environment: UPI environment simulator (used as template)
        """
        self.detector = detector
        self.environment = environment  # Used as template for creating fresh environments
        self.campaign_generator = CampaignGenerator()

    def _create_fresh_environment(self):
        """
        Create a fresh UPI environment for campaign isolation.

        This prevents velocity accumulation artifacts by ensuring each
        campaign is evaluated independently without transaction history
        from previous campaigns.

        Returns:
            Fresh UPIEnvironment instance with same detector and config
        """
        from src.environment import UPIEnvironment
        return UPIEnvironment(
            threshold_config=self.environment.threshold_config,
            fraud_detector=self.detector
        )

    def run_scenario_s1(
        self,
        num_campaigns: int = 100,
        accounts: List[str] = None,
        verbose: bool = False
    ) -> Dict:
        """
        S1: Known Fraud + Static Attacker

        Baseline scenario - detector should perform well.
        """
        if accounts is None:
            accounts = self._generate_test_accounts()

        campaigns = []

        for i in range(num_campaigns):
            # Create FRESH environment for each campaign to avoid velocity accumulation
            fresh_environment = self._create_fresh_environment()

            campaign = self.campaign_generator.create_known_fraud_campaign()
            attacker = StaticAttacker(fraud_type="known")
            executor = CampaignExecutor(self.detector, fresh_environment, attacker)

            completed_campaign = executor.execute_campaign(
                campaign,
                accounts,
                verbose=verbose and i == 0  # Verbose only for first
            )
            campaigns.append(completed_campaign)

        results = CampaignMetrics.generate_summary(campaigns, "S1: Known + Static")
        return results

    def run_scenario_s2(
        self,
        num_campaigns: int = 100,
        accounts: List[str] = None,
        verbose: bool = False
    ) -> Dict:
        """
        S2: Known Fraud + Adaptive Attacker

        Tests adaptive behavior on known fraud patterns.
        """
        if accounts is None:
            accounts = self._generate_test_accounts()

        campaigns = []

        for i in range(num_campaigns):
            # Create FRESH environment for each campaign to avoid velocity accumulation
            fresh_environment = self._create_fresh_environment()

            campaign = self.campaign_generator.create_known_fraud_campaign()
            attacker = AdaptiveAttacker(fraud_type="known")
            executor = CampaignExecutor(self.detector, fresh_environment, attacker)

            completed_campaign = executor.execute_campaign(
                campaign,
                accounts,
                verbose=verbose and i == 0
            )
            campaigns.append(completed_campaign)

        results = CampaignMetrics.generate_summary(campaigns, "S2: Known + Adaptive")
        return results

    def run_scenario_s3(
        self,
        num_campaigns: int = 100,
        accounts: List[str] = None,
        verbose: bool = False
    ) -> Dict:
        """
        S3: Unknown Fraud + Static Attacker

        Tests detector on unseen fraud patterns.
        """
        if accounts is None:
            accounts = self._generate_test_accounts()

        campaigns = []

        for i in range(num_campaigns):
            # Create FRESH environment for each campaign to avoid velocity accumulation
            fresh_environment = self._create_fresh_environment()

            campaign = self.campaign_generator.create_unknown_fraud_campaign()
            attacker = StaticAttacker(fraud_type="unknown")
            executor = CampaignExecutor(self.detector, fresh_environment, attacker)

            completed_campaign = executor.execute_campaign(
                campaign,
                accounts,
                verbose=verbose and i == 0
            )
            campaigns.append(completed_campaign)

        results = CampaignMetrics.generate_summary(campaigns, "S3: Unknown + Static")
        return results

    def run_scenario_s4(
        self,
        num_campaigns: int = 100,
        accounts: List[str] = None,
        verbose: bool = False
    ) -> Dict:
        """
        S4: Unknown Fraud + Adaptive Attacker

        PRIMARY STRESS TEST: Unknown patterns + adaptive behavior.
        This is the main research contribution.
        """
        if accounts is None:
            accounts = self._generate_test_accounts()

        campaigns = []

        for i in range(num_campaigns):
            # Create FRESH environment for each campaign to avoid velocity accumulation
            fresh_environment = self._create_fresh_environment()

            campaign = self.campaign_generator.create_unknown_fraud_campaign()
            attacker = AdaptiveAttacker(fraud_type="unknown")
            executor = CampaignExecutor(self.detector, fresh_environment, attacker)

            completed_campaign = executor.execute_campaign(
                campaign,
                accounts,
                verbose=verbose and i == 0
            )
            campaigns.append(completed_campaign)

        results = CampaignMetrics.generate_summary(campaigns, "S4: Unknown + Adaptive")
        return results

    def run_all_scenarios(
        self,
        num_campaigns: int = 100,
        save_results: bool = True,
        detector_name: str = "XGBoost"
    ) -> Dict[str, Dict]:
        """
        Run all four scenarios and compare results.

        Args:
            num_campaigns: Number of campaigns per scenario
            save_results: Save results to JSON files
            detector_name: Name of detector for result naming

        Returns:
            Dictionary with results for all scenarios
        """
        print("Running all scenarios...")
        print(f"Campaigns per scenario: {num_campaigns}\n")

        accounts = self._generate_test_accounts()

        results = {}

        print("Running S1: Known + Static...")
        results['S1'] = self.run_scenario_s1(num_campaigns, accounts)

        print("Running S2: Known + Adaptive...")
        results['S2'] = self.run_scenario_s2(num_campaigns, accounts)

        print("Running S3: Unknown + Static...")
        results['S3'] = self.run_scenario_s3(num_campaigns, accounts)

        print("Running S4: Unknown + Adaptive (PRIMARY STRESS TEST)...")
        results['S4'] = self.run_scenario_s4(num_campaigns, accounts)

        if save_results:
            self._save_results(results, detector_name=detector_name)

        self._print_comparison(results)

        return results

    def _generate_test_accounts(self, num_accounts: int = 20) -> List[str]:
        """Generate test VPA addresses."""
        return [f"user{i}@upi" for i in range(num_accounts)]

    def _save_results(self, results: Dict[str, Dict], detector_name: str = "XGBoost"):
        """Save results to JSON files."""
        results_dir = Path("results/metrics")
        results_dir.mkdir(parents=True, exist_ok=True)

        # Create detector-specific subdirectory
        detector_slug = detector_name.lower().replace(' ', '_')
        detector_dir = results_dir / detector_slug
        detector_dir.mkdir(parents=True, exist_ok=True)

        for scenario, data in results.items():
            # Save in detector-specific directory
            filepath = detector_dir / f"{scenario}_results.json"
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Saved {scenario} results to {filepath}")

            # Also save in main directory for backward compatibility
            main_filepath = results_dir / f"{scenario}_results.json"
            with open(main_filepath, 'w') as f:
                json.dump(data, f, indent=2)

    def _print_comparison(self, results: Dict[str, Dict]):
        """Print comparison table."""
        print("\n" + "="*80)
        print("SCENARIO COMPARISON")
        print("="*80)

        headers = ["Metric", "S1", "S2", "S3", "S4"]

        metrics = [
            ("Campaign Success Rate", "campaign_success_rate", "{:.1%}"),
            ("Avg Detection Time (s)", "avg_detection_time_sec", "{:.2f}"),
            ("Avg Intervention Time (s)", "avg_intervention_time_sec", "{:.2f}"),
            ("Avg Financial Exposure", "avg_financial_exposure", "₹{:,.0f}"),
            ("Total Exposure", "total_financial_exposure", "₹{:,.0f}"),
        ]

        # Print header
        print(f"\n{headers[0]:<30} {headers[1]:<12} {headers[2]:<12} {headers[3]:<12} {headers[4]:<12}")
        print("-" * 80)

        # Print metrics
        for metric_name, key, fmt in metrics:
            values = [results[s].get(key, 0) for s in ['S1', 'S2', 'S3', 'S4']]
            formatted = [fmt.format(v) for v in values]
            print(f"{metric_name:<30} {formatted[0]:<12} {formatted[1]:<12} {formatted[2]:<12} {formatted[3]:<12}")

        print("="*80 + "\n")
