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
            return 0.0

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
            return 0.0

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
        return {
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
            )
        }
