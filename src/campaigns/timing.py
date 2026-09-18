"""
Campaign timing models for realistic velocity generation.

Each campaign family has characteristic temporal behavior that produces
realistic transaction velocity when transactions are executed with proper timing.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
import random
from typing import Optional

# Import CampaignFamily from generator to avoid duplicate enum definition
from src.campaigns.generator import CampaignFamily


@dataclass
class TimingModel:
    """
    Timing model for a campaign family.

    Defines the temporal characteristics that produce realistic velocity.
    """
    family: CampaignFamily

    # Inter-transaction interval range (seconds)
    min_interval_seconds: float
    max_interval_seconds: float

    # Expected transactions per hour (for validation)
    expected_velocity_range: tuple  # (min, max)

    # Description
    description: str


# Timing models for each campaign family
TIMING_MODELS = {
    CampaignFamily.HIGH_VALUE_BURST: TimingModel(
        family=CampaignFamily.HIGH_VALUE_BURST,
        min_interval_seconds=180,   # 3 minutes minimum
        max_interval_seconds=900,   # 15 minutes maximum
        expected_velocity_range=(4, 12),  # High velocity (4-12 txns/hour)
        description="High-velocity burst: rapid succession of large transactions"
    ),

    CampaignFamily.SLOW_DRAIN: TimingModel(
        family=CampaignFamily.SLOW_DRAIN,
        min_interval_seconds=600,   # 10 minutes minimum
        max_interval_seconds=1800,  # 30 minutes maximum
        expected_velocity_range=(2, 6),   # Moderate velocity (2-6 txns/hour)
        description="Slow drain: sustained moderate-velocity stream"
    ),

    CampaignFamily.GRADUAL_ESCALATION: TimingModel(
        family=CampaignFamily.GRADUAL_ESCALATION,
        min_interval_seconds=300,   # 5 minutes minimum
        max_interval_seconds=1200,  # 20 minutes maximum
        expected_velocity_range=(3, 9),   # Moderate-high velocity (3-9 txns/hour)
        description="Gradual escalation: progressive testing with moderate pacing"
    ),

    CampaignFamily.BENEFICIARY_HOPPING: TimingModel(
        family=CampaignFamily.BENEFICIARY_HOPPING,
        min_interval_seconds=240,   # 4 minutes minimum
        max_interval_seconds=1000,  # 16.7 minutes maximum
        expected_velocity_range=(3, 10),  # Moderate-high velocity (3-10 txns/hour)
        description="Beneficiary hopping: rapid rotation with moderate pacing"
    ),
}


class CampaignTimer:
    """
    Manages transaction timing for a campaign.

    Generates realistic timestamps based on campaign family timing model.
    """

    def __init__(
        self,
        family: CampaignFamily,
        start_time: Optional[datetime] = None,
        seed: Optional[int] = None
    ):
        """
        Initialize campaign timer.

        Args:
            family: Campaign family
            start_time: Campaign start time (default: now)
            seed: Random seed for reproducible timing
        """
        self.family = family
        self.timing_model = TIMING_MODELS[family]
        self.current_time = start_time or datetime.now()
        self.transaction_count = 0

        # Use seeded random for reproducible timing
        self.random = random.Random(seed)

    def next_transaction_time(self) -> datetime:
        """
        Get timestamp for next transaction.

        Uses timing model to generate realistic inter-transaction interval.

        Returns:
            Timestamp for next transaction
        """
        if self.transaction_count == 0:
            # First transaction: use start time
            timestamp = self.current_time
        else:
            # Subsequent transactions: add random interval
            interval_seconds = self.random.uniform(
                self.timing_model.min_interval_seconds,
                self.timing_model.max_interval_seconds
            )
            self.current_time += timedelta(seconds=interval_seconds)
            timestamp = self.current_time

        self.transaction_count += 1
        return timestamp

    def get_expected_velocity(self) -> tuple:
        """Get expected velocity range for this family."""
        return self.timing_model.expected_velocity_range

    def get_description(self) -> str:
        """Get timing model description."""
        return self.timing_model.description

    def reset(self, start_time: Optional[datetime] = None):
        """Reset timer for new campaign."""
        self.current_time = start_time or datetime.now()
        self.transaction_count = 0


def get_timing_model(family: CampaignFamily) -> TimingModel:
    """Get timing model for a campaign family."""
    return TIMING_MODELS[family]


def estimate_campaign_duration(
    family: CampaignFamily,
    num_transactions: int
) -> float:
    """
    Estimate campaign duration in seconds.

    Args:
        family: Campaign family
        num_transactions: Expected number of transactions

    Returns:
        Estimated duration in seconds
    """
    model = TIMING_MODELS[family]
    avg_interval = (model.min_interval_seconds + model.max_interval_seconds) / 2
    return avg_interval * (num_transactions - 1)  # n-1 intervals for n transactions
