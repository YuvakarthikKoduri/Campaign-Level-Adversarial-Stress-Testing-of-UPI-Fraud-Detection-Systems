"""
Campaign generator for fraud scenarios.

A campaign is a sequence of transactions with a specific objective.
"""
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from enum import Enum


class CampaignStatus(Enum):
    """Campaign status."""
    ACTIVE = "ACTIVE"
    SUCCESS = "SUCCESS"
    DETECTED = "DETECTED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


class Campaign:
    """Represents a fraud campaign."""

    def __init__(
        self,
        campaign_id: str,
        attacker_id: str,
        objective: str,
        target_amount: float,
        fraud_type: str = "known"
    ):
        self.campaign_id = campaign_id
        self.attacker_id = attacker_id
        self.objective = objective
        self.target_amount = target_amount
        self.fraud_type = fraud_type  # "known" or "unknown"
        self.transactions = []
        self.status = CampaignStatus.ACTIVE
        self.total_amount_moved = 0.0
        self.total_amount_blocked = 0.0
        self.created_at = datetime.now()
        self.completed_at = None
        self.detection_time = None  # Time to first detection
        self.intervention_time = None  # Time to campaign termination

    def add_transaction(self, transaction: Dict):
        """Add a transaction to the campaign."""
        self.transactions.append(transaction)

        # Update totals based on decision
        decision = transaction.get("decision", "UNKNOWN")
        amount = transaction.get("amount", 0)

        if decision == "ALLOW":
            self.total_amount_moved += amount
        elif decision in ["FLAG", "BLOCK"]:
            self.total_amount_blocked += amount

            # Record first detection time
            if self.detection_time is None and decision in ["FLAG", "BLOCK"]:
                self.detection_time = (
                    datetime.now() - self.created_at
                ).total_seconds()

            # Campaign terminated on BLOCK
            if decision == "BLOCK":
                self.status = CampaignStatus.BLOCKED
                self.intervention_time = (
                    datetime.now() - self.created_at
                ).total_seconds()
                self.completed_at = datetime.now()

    def is_complete(self) -> bool:
        """Check if campaign is complete."""
        if self.status in [CampaignStatus.BLOCKED, CampaignStatus.FAILED]:
            return True
        if self.total_amount_moved >= self.target_amount:
            self.status = CampaignStatus.SUCCESS
            self.completed_at = datetime.now()
            return True
        return False

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "campaign_id": self.campaign_id,
            "attacker_id": self.attacker_id,
            "objective": self.objective,
            "target_amount": self.target_amount,
            "fraud_type": self.fraud_type,
            "status": self.status.value,
            "total_amount_moved": self.total_amount_moved,
            "total_amount_blocked": self.total_amount_blocked,
            "num_transactions": len(self.transactions),
            "detection_time": self.detection_time,
            "intervention_time": self.intervention_time,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class CampaignGenerator:
    """Generates fraud campaigns."""

    def __init__(self):
        self.campaigns = []

    def create_known_fraud_campaign(
        self,
        target_amount: float = 50000,
        attacker_id: Optional[str] = None
    ) -> Campaign:
        """
        Create a known fraud campaign.

        Known fraud uses patterns similar to training data:
        - High transaction amounts
        - High velocity
        - New beneficiaries
        """
        if attacker_id is None:
            attacker_id = f"attacker_{uuid.uuid4().hex[:8]}"

        campaign = Campaign(
            campaign_id=f"known_{uuid.uuid4().hex[:8]}",
            attacker_id=attacker_id,
            objective="Move funds using known fraud patterns",
            target_amount=target_amount,
            fraud_type="known"
        )

        self.campaigns.append(campaign)
        return campaign

    def create_unknown_fraud_campaign(
        self,
        target_amount: float = 50000,
        attacker_id: Optional[str] = None
    ) -> Campaign:
        """
        Create an unknown fraud campaign.

        Unknown fraud uses patterns different from training data:
        - Small transaction amounts
        - Slower timing
        - Multiple intermediate accounts
        - Gradual movement
        """
        if attacker_id is None:
            attacker_id = f"attacker_{uuid.uuid4().hex[:8]}"

        campaign = Campaign(
            campaign_id=f"unknown_{uuid.uuid4().hex[:8]}",
            attacker_id=attacker_id,
            objective="Move funds using previously unseen patterns",
            target_amount=target_amount,
            fraud_type="unknown"
        )

        self.campaigns.append(campaign)
        return campaign

    def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """Get a campaign by ID."""
        for campaign in self.campaigns:
            if campaign.campaign_id == campaign_id:
                return campaign
        return None
