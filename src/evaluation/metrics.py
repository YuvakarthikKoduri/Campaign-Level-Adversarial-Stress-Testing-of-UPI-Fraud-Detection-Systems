"""
Campaign-level evaluation metrics.
"""
from typing import List, Dict
import numpy as np


class CampaignMetrics:
    """Calculate campaign-level metrics."""

    @staticmethod
    def campaign_success_rate(campaigns: List['Campaign']) -> float:
        """
        Calculate campaign success rate.

        Args:
            campaigns: List of completed campaigns

        Returns:
            Success rate (0.0 to 1.0)
        """
        if not campaigns:
            return 0.0

        successful = sum(
            1 for c in campaigns
            if c.status.value == "SUCCESS"
        )

        return successful / len(campaigns)

    @staticmethod
    def average_detection_time(campaigns: List['Campaign']) -> float:
        """
        Calculate average time to first detection.

        Args:
            campaigns: List of campaigns

        Returns:
            Average detection time in seconds
        """
        detection_times = [
            c.detection_time for c in campaigns
            if c.detection_time is not None
        ]

        if not detection_times:
            return None

        return np.mean(detection_times)

    @staticmethod
    def average_intervention_time(campaigns: List['Campaign']) -> float:
        """
        Calculate average time to campaign termination.

        Args:
            campaigns: List of campaigns

        Returns:
            Average intervention time in seconds
        """
        intervention_times = [
            c.intervention_time for c in campaigns
            if c.intervention_time is not None
        ]

        if not intervention_times:
            return None

        return np.mean(intervention_times)

    @staticmethod
    def average_financial_exposure(campaigns: List['Campaign']) -> float:
        """
        Calculate average money exposed before intervention.

        Financial exposure = total amount moved before first BLOCK

        Args:
            campaigns: List of campaigns

        Returns:
            Average financial exposure
        """
        exposures = [c.total_amount_moved for c in campaigns]

        if not exposures:
            return 0.0

        return np.mean(exposures)

    @staticmethod
    def total_financial_exposure(campaigns: List['Campaign']) -> float:
        """
        Calculate total money exposed across all campaigns.

        Args:
            campaigns: List of campaigns

        Returns:
            Total financial exposure
        """
        return sum(c.total_amount_moved for c in campaigns)

    @staticmethod
    def detector_degradation(
        normal_f1: float,
        under_attack_f1: float
    ) -> float:
        """
        Calculate detector performance degradation.

        Args:
            normal_f1: F1 score under normal conditions
            under_attack_f1: F1 score under attack

        Returns:
            Degradation (positive value means performance dropped)
        """
        return normal_f1 - under_attack_f1

    @staticmethod
    def generate_summary(
        campaigns: List['Campaign'],
        scenario_name: str = "Unknown"
    ) -> Dict:
        """
        Generate comprehensive metrics summary.

        Args:
            campaigns: List of campaigns
            scenario_name: Name of the scenario

        Returns:
            Dictionary with all metrics
        """
        transactions = [t for c in campaigns for t in c.transactions]
        legitimate = [t for c in campaigns if not c.is_fraud for t in c.transactions]
        fraudulent = [c for c in campaigns if c.is_fraud]
        rate = lambda count, total: count / total if total else None
        summary = {
            "metric_version": "corrected-v2",
            "scenario": scenario_name,
            "num_campaigns": len(campaigns),
            "campaign_success_rate": CampaignMetrics.campaign_success_rate(campaigns),
            "avg_detection_time_sec": CampaignMetrics.average_detection_time(campaigns),
            "avg_intervention_time_sec": CampaignMetrics.average_intervention_time(campaigns),
            "avg_financial_exposure": CampaignMetrics.average_financial_exposure(campaigns),
            "total_financial_exposure": CampaignMetrics.total_financial_exposure(campaigns),
            "successful_campaigns": sum(
                1 for c in campaigns if c.status.value == "SUCCESS"
            ),
            "blocked_campaigns": sum(
                1 for c in campaigns if c.status.value == "BLOCKED"
            ),
            "detected_campaigns": sum(
                1 for c in campaigns if c.detection_time is not None
            ),
            "total_attempted_amount": sum(c.total_attempted_amount for c in campaigns),
            "detection_censored_campaigns": sum(c.detection_time is None for c in campaigns),
            "intervention_censored_campaigns": sum(c.intervention_time is None for c in campaigns),
            "timed_out_campaigns": sum(c.status.value == "TIMED_OUT" for c in campaigns),
            "invalid_campaigns": sum(c.status.value == "INVALID" for c in campaigns),
            "failed_campaigns": sum(c.status.value == "FAILED" for c in campaigns),
            "transaction_count": len(transactions),
            "transaction_detection_rate": rate(sum(t.get("decision") in ("FLAG", "BLOCK")
                                                    for t in transactions), len(transactions)),
            "transaction_block_rate": rate(sum(t.get("decision") == "BLOCK"
                                                for t in transactions), len(transactions)),
            "legitimate_transaction_block_rate": rate(sum(t.get("decision") == "BLOCK"
                                                           for t in legitimate), len(legitimate)),
            "legitimate_transaction_flag_rate": rate(sum(t.get("decision") == "FLAG"
                                                          for t in legitimate), len(legitimate)),
            "legitimate_amount_blocked": sum(t.get("amount", 0) for t in legitimate
                                             if t.get("decision") == "BLOCK"),
            "legitimate_transaction_count": len(legitimate),
            "fraud_campaign_count": len(fraudulent),
            "fraud_campaign_success_rate": (CampaignMetrics.campaign_success_rate(fraudulent)
                                            if fraudulent else None),
            "total_exposure_before_detection": sum(
                c.exposure_before_detection if c.exposure_before_detection is not None
                else c.total_amount_moved for c in campaigns),
            "total_exposure_before_intervention": sum(
                c.exposure_before_intervention if c.exposure_before_intervention is not None
                else c.total_amount_moved for c in campaigns),
        }
        assert summary["total_financial_exposure"] <= summary["total_attempted_amount"] + 1e-6
        return summary
