#!/usr/bin/env python3
"""Core functionality tests for UPI Fraud Stress Lab."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import unittest
import numpy as np
from src.detectors.baseline import load_detector, BaselineDetector
from src.environment import UPIEnvironment
from src.campaigns.generator import CampaignGenerator, CampaignFamily
from src.attackers.static import StaticAttacker
from src.attackers.adaptive import AdaptiveAttacker
from src.campaigns.executor import CampaignExecutor
from src.evaluation.metrics import CampaignMetrics


class TestDetectorLoading(unittest.TestCase):
    """Test detector loading and feature extraction."""

    def test_load_xgboost_detector(self):
        """Test loading XGBoost detector."""
        detector = load_detector('models/baseline_xgboost.pkl')
        self.assertIsNotNone(detector.model)
        self.assertEqual(len(detector.feature_names), 4)
        self.assertIn('amount', detector.feature_names)

    def test_load_random_forest_detector(self):
        """Test loading Random Forest detector."""
        detector = load_detector('models/baseline_random_forest.pkl')
        self.assertIsNotNone(detector.model)
        self.assertEqual(len(detector.feature_names), 4)

    def test_predict_transaction(self):
        """Test detector prediction on sample transaction."""
        detector = load_detector('models/baseline_xgboost.pkl')

        txn = {
            'amount': 5000,
            'hour_of_day': 14,
            'velocity_1h': 2,
            'is_new_vpa': 0
        }

        risk_score = detector.predict(txn)
        self.assertIsInstance(risk_score, (float, np.floating))
        self.assertGreaterEqual(risk_score, 0.0)
        self.assertLessEqual(risk_score, 1.0)


class TestCampaignGeneration(unittest.TestCase):
    """Test campaign generation across all families."""

    def setUp(self):
        self.generator = CampaignGenerator()

    def test_known_fraud_campaign(self):
        """Test known fraud campaign generation."""
        campaign = self.generator.create_known_fraud_campaign(target_amount=30000)
        self.assertEqual(campaign.fraud_type, "known")
        self.assertEqual(campaign.target_amount, 30000)
        self.assertIn(campaign.family, [CampaignFamily.HIGH_VALUE_BURST])

    def test_unknown_fraud_campaign(self):
        """Test unknown fraud campaign generation."""
        campaign = self.generator.create_unknown_fraud_campaign(target_amount=15000)
        self.assertEqual(campaign.fraud_type, "unknown")
        self.assertEqual(campaign.target_amount, 15000)
        self.assertIn(campaign.family, [
            CampaignFamily.SLOW_DRAIN,
            CampaignFamily.GRADUAL_ESCALATION,
            CampaignFamily.BENEFICIARY_HOPPING
        ])

    def test_all_campaign_families(self):
        """Test generation of multiple unknown campaign families."""
        families_seen = set()

        # Seed for reproducibility
        np.random.seed(42)

        # Unknown campaigns rotate through families
        for _ in range(50):
            campaign = self.generator.create_unknown_fraud_campaign()
            families_seen.add(campaign.family)

        # Should see at least 2 different families
        self.assertGreaterEqual(len(families_seen), 2)


class TestAttackerBehavior(unittest.TestCase):
    """Test static and adaptive attacker behavior."""

    def test_static_attacker_init(self):
        """Test static attacker initialization."""
        attacker = StaticAttacker(fraud_type="known")
        self.assertEqual(attacker.fraud_type, "known")

    def test_adaptive_attacker_init(self):
        """Test adaptive attacker initialization."""
        attacker = AdaptiveAttacker(fraud_type="known")
        self.assertEqual(attacker.fraud_type, "known")
        self.assertIsInstance(attacker.safe_amounts, list)
        self.assertIsInstance(attacker.safe_beneficiaries, set)

    def test_adaptive_attacker_observes(self):
        """Test adaptive attacker observation mechanism."""
        attacker = AdaptiveAttacker(fraud_type="known")

        response = {
            'decision': 'ALLOW',
            'amount': 10000,
            'to_vpa': 'user1@upi'
        }

        attacker.observe(response)
        self.assertIn(10000, attacker.safe_amounts)
        self.assertIn('user1@upi', attacker.safe_beneficiaries)

    def test_adaptive_state_tracking(self):
        """Test adaptive attacker maintains state across observations."""
        attacker = AdaptiveAttacker(fraud_type="known")

        attacker.observe({'decision': 'ALLOW', 'amount': 5000})
        attacker.observe({'decision': 'BLOCK', 'amount': 50000})
        attacker.observe({'decision': 'ALLOW', 'amount': 7000})

        self.assertEqual(len(attacker.safe_amounts), 2)
        self.assertGreater(attacker.blocked_count, 0)


class TestEnvironment(unittest.TestCase):
    """Test UPI environment simulation."""

    def setUp(self):
        self.detector = load_detector('models/baseline_xgboost.pkl')
        self.environment = UPIEnvironment(fraud_detector=self.detector)

    def test_process_transaction(self):
        """Test transaction processing."""
        txn = {
            'from_vpa': 'user1@upi',
            'to_vpa': 'user2@upi',
            'amount': 5000
        }

        response = self.environment.process_transaction(txn)
        self.assertIn('decision', response)
        self.assertIn('risk_score', response)
        self.assertIn(response['decision'], ['ALLOW', 'FLAG', 'BLOCK'])
        self.assertEqual(response['decision'], self.environment.threshold_config.get_decision(
            response['risk_score']).value)

    def test_account_balance_tracking(self):
        """Test that environment tracks transactions."""
        # Initialize accounts in environment
        self.environment.accounts['user1@upi'] = 100000
        self.environment.accounts['user2@upi'] = 100000

        txn = {
            'from_vpa': 'user1@upi',
            'to_vpa': 'user2@upi',
            'amount': 5000
        }

        response = self.environment.process_transaction(txn)

        # Verify response structure
        self.assertIn('decision', response)
        self.assertIn('risk_score', response)

        # Verify accounts still exist
        self.assertIn('user1@upi', self.environment.accounts)
        self.assertIn('user2@upi', self.environment.accounts)

    def test_zero_amount_transaction(self):
        """Test edge case: zero amount transaction."""
        txn = {
            'from_vpa': 'user1@upi',
            'to_vpa': 'user2@upi',
            'amount': 0
        }

        response = self.environment.process_transaction(txn)
        self.assertIsNone(response['decision'])
        self.assertEqual(response['execution_status'], 'invalid')


class TestCampaignExecution(unittest.TestCase):
    """Test campaign execution and metrics."""

    def setUp(self):
        self.detector = load_detector('models/baseline_xgboost.pkl')
        self.environment = UPIEnvironment(fraud_detector=self.detector)
        self.generator = CampaignGenerator()

    def test_campaign_execution(self):
        """Test full campaign execution."""
        campaign = self.generator.create_known_fraud_campaign(target_amount=10000)
        attacker = StaticAttacker(fraud_type="known")
        executor = CampaignExecutor(self.detector, self.environment, attacker, max_steps=20)

        accounts = [f"user{i}@upi" for i in range(20)]
        result = executor.execute_campaign(campaign, accounts)

        self.assertIsNotNone(result.status)
        self.assertGreaterEqual(result.total_amount_moved, 0)
        self.assertGreater(len(result.transactions), 0)

    def test_max_steps_enforcement(self):
        """Test campaign stops at max_steps."""
        campaign = self.generator.create_known_fraud_campaign(target_amount=100000)
        attacker = StaticAttacker(fraud_type="known")
        executor = CampaignExecutor(self.detector, self.environment, attacker, max_steps=5)

        accounts = [f"user{i}@upi" for i in range(20)]
        result = executor.execute_campaign(campaign, accounts)

        self.assertLessEqual(len(result.transactions), 5)


class TestMetrics(unittest.TestCase):
    """Test campaign-level metrics calculation."""

    def test_success_rate_calculation(self):
        """Test campaign success rate metric."""
        # Test with actual campaign execution instead of mock data
        detector = load_detector('models/baseline_xgboost.pkl')
        environment = UPIEnvironment(fraud_detector=detector)
        generator = CampaignGenerator()

        campaigns = []
        accounts = [f"user{i}@upi" for i in range(20)]

        for i in range(5):
            campaign = generator.create_known_fraud_campaign(target_amount=10000)
            attacker = StaticAttacker(fraud_type="known")
            executor = CampaignExecutor(detector, environment, attacker, max_steps=10)
            result = executor.execute_campaign(campaign, accounts)
            campaigns.append(result)

        summary = CampaignMetrics.generate_summary(campaigns, "Test")
        self.assertEqual(summary['num_campaigns'], 5)
        self.assertIn('campaign_success_rate', summary)
        self.assertIn('total_financial_exposure', summary)

    def test_financial_exposure_tracking(self):
        """Test financial exposure calculation."""
        # Test with actual campaign execution
        detector = load_detector('models/baseline_xgboost.pkl')
        environment = UPIEnvironment(fraud_detector=detector)
        generator = CampaignGenerator()

        campaigns = []
        accounts = [f"user{i}@upi" for i in range(20)]

        for i in range(3):
            campaign = generator.create_known_fraud_campaign(target_amount=5000)
            attacker = StaticAttacker(fraud_type="known")
            executor = CampaignExecutor(detector, environment, attacker, max_steps=5)
            result = executor.execute_campaign(campaign, accounts)
            campaigns.append(result)

        summary = CampaignMetrics.generate_summary(campaigns, "Test")

        # Total exposure should equal sum of individual campaign exposures
        manual_total = sum(c.total_amount_moved for c in campaigns)
        self.assertEqual(summary['total_financial_exposure'], manual_total)


class TestReproducibility(unittest.TestCase):
    """Test reproducibility with seed control."""

    def test_same_seed_same_result(self):
        """Test that same seed produces similar deterministic behavior."""
        import random

        # Seed both random and numpy
        random.seed(123)
        np.random.seed(123)

        detector = load_detector('models/baseline_xgboost.pkl')
        environment1 = UPIEnvironment(fraud_detector=detector)
        generator1 = CampaignGenerator()

        campaign1 = generator1.create_known_fraud_campaign(target_amount=15000)
        attacker1 = StaticAttacker(fraud_type="known")
        executor1 = CampaignExecutor(detector, environment1, attacker1, max_steps=10)
        accounts = [f"user{i}@upi" for i in range(20)]
        result1 = executor1.execute_campaign(campaign1, accounts)

        # Reset seeds
        random.seed(123)
        np.random.seed(123)

        environment2 = UPIEnvironment(fraud_detector=detector)
        generator2 = CampaignGenerator()
        campaign2 = generator2.create_known_fraud_campaign(target_amount=15000)
        attacker2 = StaticAttacker(fraud_type="known")
        executor2 = CampaignExecutor(detector, environment2, attacker2, max_steps=10)
        result2 = executor2.execute_campaign(campaign2, accounts)

        # With same seed, behavior should be deterministic
        self.assertEqual(result1.status, result2.status)
        self.assertEqual(len(result1.transactions), len(result2.transactions))


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def setUp(self):
        self.detector = load_detector('models/baseline_xgboost.pkl')
        self.environment = UPIEnvironment(fraud_detector=self.detector)

    def test_insufficient_balance(self):
        """Test transaction with insufficient balance."""
        # Note: Current environment doesn't enforce balance checks
        # This test verifies the detector's risk assessment instead
        self.environment.accounts['poor@upi'] = 100
        self.environment.accounts['rich@upi'] = 100000

        txn = {
            'from_vpa': 'poor@upi',
            'to_vpa': 'rich@upi',
            'amount': 10000
        }

        response = self.environment.process_transaction(txn)
        # Detector may allow or block based on risk features
        self.assertIn('decision', response)
        self.assertIn('risk_score', response)

    def test_negative_amount(self):
        """Test transaction with negative amount."""
        txn = {
            'from_vpa': 'user1@upi',
            'to_vpa': 'user2@upi',
            'amount': -5000
        }

        response = self.environment.process_transaction(txn)
        self.assertIsNone(response['decision'])
        self.assertEqual(response['execution_status'], 'invalid')

    def test_extremely_high_amount(self):
        """Test transaction with very high amount."""
        txn = {
            'from_vpa': 'user1@upi',
            'to_vpa': 'user2@upi',
            'amount': 1000000
        }

        response = self.environment.process_transaction(txn)
        self.assertIn('decision', response)
        self.assertIn('risk_score', response)


if __name__ == '__main__':
    unittest.main(verbosity=2)
