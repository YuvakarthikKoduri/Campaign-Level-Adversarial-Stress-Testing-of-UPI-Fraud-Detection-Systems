"""
Campaign generator for fraud scenarios.

A campaign is a sequence of transactions with a specific objective.
Each campaign family represents a DISTINCT behavioral mechanism.
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


class CampaignFamily(Enum):
    """
    Campaign families represent distinct fraud mechanisms.

    Each family differs in BEHAVIOR, not just parameters:
    - HIGH_VALUE_BURST: Large amounts, fast execution (training-like)
    - SLOW_DRAIN: Small repeated amounts over time
    - GRADUAL_ESCALATION: Start small, progressively increase
    - BENEFICIARY_HOPPING: Rapid beneficiary rotation
    """
    HIGH_VALUE_BURST = "high_value_burst"
    SLOW_DRAIN = "slow_drain"
    GRADUAL_ESCALATION = "gradual_escalation"
    BENEFICIARY_HOPPING = "beneficiary_hopping"


class Campaign:
    """Represents a fraud campaign."""

    def __init__(
        self,
        campaign_id: str,
        attacker_id: str,
        objective: str,
        target_amount: float,
        fraud_type: str = "known",
        family: Optional[CampaignFamily] = None
    ):
        self.campaign_id = campaign_id
        self.attacker_id = attacker_id
        self.objective = objective
        self.target_amount = target_amount
        self.fraud_type = fraud_type  # "known" or "unknown"
        self.family = family  # Campaign behavioral family
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
            "family": self.family.value if self.family else None,
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
    """Generates fraud campaigns with distinct behavioral families."""

    def __init__(self):
        self.campaigns = []

    def create_known_fraud_campaign(
        self,
        target_amount: float = None,
        attacker_id: Optional[str] = None
    ) -> Campaign:
        """
        Create a known fraud campaign.

        Known fraud uses patterns similar to training data:
        - High transaction amounts (₹10,000-50,000 per attempt)
        - High velocity
        - New beneficiaries

        Default target: ₹30,000 (achievable in 1-3 successful transactions)
        Family: HIGH_VALUE_BURST
        """
        if target_amount is None:
            # Realistic target: 1-3 successful high-value transactions
            # Base transaction ≈ ₹25,000, so target of ₹30,000 is feasible
            target_amount = 30000

        if attacker_id is None:
            attacker_id = f"attacker_{uuid.uuid4().hex[:8]}"

        campaign = Campaign(
            campaign_id=f"known_{uuid.uuid4().hex[:8]}",
            attacker_id=attacker_id,
            objective="Move funds using known fraud patterns",
            target_amount=target_amount,
            fraud_type="known",
            family=CampaignFamily.HIGH_VALUE_BURST
        )

        self.campaigns.append(campaign)
        return campaign

    def create_unknown_fraud_campaign(
        self,
        target_amount: float = None,
        attacker_id: Optional[str] = None
    ) -> Campaign:
        """
        Create an unknown fraud campaign.

        Unknown fraud uses patterns different from training data:
        - Small transaction amounts (₹1,000-5,000 per attempt)
        - Slower timing
        - Multiple intermediate accounts
        - Gradual movement

        Default target: ₹15,000 (achievable in 3-15 successful small transactions)
        Family: SLOW_DRAIN
        """
        if target_amount is None:
            # Realistic target: multiple successful small transactions
            # Base transaction ≈ ₹3,000, so target of ₹15,000 needs 5 successes
            target_amount = 15000

        if attacker_id is None:
            attacker_id = f"attacker_{uuid.uuid4().hex[:8]}"

        campaign = Campaign(
            campaign_id=f"unknown_{uuid.uuid4().hex[:8]}",
            attacker_id=attacker_id,
            objective="Move funds using previously unseen patterns",
            target_amount=target_amount,
            fraud_type="unknown",
            family=CampaignFamily.SLOW_DRAIN
        )

        self.campaigns.append(campaign)
        return campaign

    def create_gradual_escalation_campaign(
        self,
        target_amount: float = None,
        attacker_id: Optional[str] = None,
        fraud_type: str = "unknown"
    ) -> Campaign:
        """
        Create a gradual escalation campaign.

        Behavioral mechanism:
        - Start with very small amounts (₹500-1,000)
        - Progressively increase amounts as detector allows
        - Test detector boundaries systematically
        - Different from training: gradual ramp-up pattern

        Default target: ₹20,000
        Family: GRADUAL_ESCALATION
        """
        if target_amount is None:
            target_amount = 20000

        if attacker_id is None:
            attacker_id = f"attacker_{uuid.uuid4().hex[:8]}"

        campaign = Campaign(
            campaign_id=f"escalation_{uuid.uuid4().hex[:8]}",
            attacker_id=attacker_id,
            objective="Test detector boundaries through gradual escalation",
            target_amount=target_amount,
            fraud_type=fraud_type,
            family=CampaignFamily.GRADUAL_ESCALATION
        )

        self.campaigns.append(campaign)
        return campaign

    def create_beneficiary_hopping_campaign(
        self,
        target_amount: float = None,
        attacker_id: Optional[str] = None,
        fraud_type: str = "unknown"
    ) -> Campaign:
        """
        Create a beneficiary hopping campaign.

        Behavioral mechanism:
        - Rapid rotation through many beneficiaries
        - Smaller amounts per beneficiary
        - Distributed pattern to avoid per-VPA velocity detection
        - Different from training: high beneficiary diversity

        Default target: ₹18,000
        Family: BENEFICIARY_HOPPING
        """
        if target_amount is None:
            target_amount = 18000

        if attacker_id is None:
            attacker_id = f"attacker_{uuid.uuid4().hex[:8]}"

        campaign = Campaign(
            campaign_id=f"hopping_{uuid.uuid4().hex[:8]}",
            attacker_id=attacker_id,
            objective="Distribute fraud across many beneficiaries",
            target_amount=target_amount,
            fraud_type=fraud_type,
            family=CampaignFamily.BENEFICIARY_HOPPING
        )

        self.campaigns.append(campaign)
        return campaign

    def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """Get a campaign by ID."""
        for campaign in self.campaigns:
            if campaign.campaign_id == campaign_id:
                return campaign
        return None
