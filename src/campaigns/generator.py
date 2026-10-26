"""
Campaign generator for fraud scenarios.

A campaign is a sequence of transactions with a specific objective.
Each campaign family represents a DISTINCT behavioral mechanism.
"""
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from enum import Enum

from src.campaigns.vpa_strategy import VPAStrategy
from src.money import add_money, at_least


class CampaignStatus(Enum):
    """Campaign status."""
    ACTIVE = "ACTIVE"
    SUCCESS = "SUCCESS"
    DETECTED = "DETECTED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    INVALID = "INVALID"


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
        family: Optional[CampaignFamily] = None,
        vpa_strategy: Optional[VPAStrategy] = None
    ):
        self.campaign_id = campaign_id
        self.attacker_id = attacker_id
        self.objective = objective
        self.target_amount = target_amount
        self.fraud_type = fraud_type  # "known" or "unknown"
        self.family = family  # Campaign behavioral family
        self.vpa_strategy = vpa_strategy  # Source VPA selection strategy
        self.transactions = []
        self.status = CampaignStatus.ACTIVE
        self.total_amount_moved = 0.0
        self.total_amount_blocked = 0.0
        self.created_at = datetime(2026, 1, 5, 12)
        self.completed_at = None
        self.detection_time = None  # Time to first detection
        self.intervention_time = None  # Time to campaign termination
        self.total_attempted_amount = 0.0
        self.exposure_before_detection = None
        self.exposure_before_intervention = None
        self.termination_reason = None
        self.is_fraud = True
        self.budget = 500000.0
        self.max_duration_seconds = 86400.0

    def add_transaction(self, transaction: Dict):
        """Add a transaction to the campaign."""
        when = transaction.get("timestamp", self.created_at)
        if isinstance(when, str):
            when = datetime.fromisoformat(when)
        if when < self.created_at:
            raise ValueError("Event precedes campaign start")
        before = self.total_amount_moved
        decision, amount = transaction.get("decision"), transaction.get("amount", 0)
        moved = transaction.get("amount_transferred", amount if decision in ("ALLOW", "FLAG") else 0)
        if not 0 <= moved <= amount:
            raise ValueError("Invalid transferred amount")
        self.transactions.append(transaction)
        self.total_attempted_amount = add_money(self.total_attempted_amount, amount)
        self.total_amount_moved = add_money(self.total_amount_moved, moved)
        if decision == "BLOCK":
            self.total_amount_blocked = add_money(self.total_amount_blocked, amount)
        if self.detection_time is None and decision in ("FLAG", "BLOCK"):
            self.detection_time = (when - self.created_at).total_seconds()
            self.exposure_before_detection = before
        if decision == "BLOCK":
            self.intervention_time = (when - self.created_at).total_seconds()
            self.exposure_before_intervention = before
            self.finalize(CampaignStatus.BLOCKED, "first_detector_block", when)
        elif at_least(self.total_amount_moved, self.target_amount):
            self.finalize(CampaignStatus.SUCCESS, "target_reached", when)

    def finalize(self, status, reason, when):
        self.status, self.termination_reason, self.completed_at = status, reason, when

    def is_complete(self) -> bool:
        """Check if campaign is complete."""
        return self.status != CampaignStatus.ACTIVE

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "campaign_id": self.campaign_id,
            "attacker_id": self.attacker_id,
            "objective": self.objective,
            "target_amount": self.target_amount,
            "fraud_type": self.fraud_type,
            "family": self.family.value if self.family else None,
            "vpa_strategy": self.vpa_strategy.value if self.vpa_strategy else None,
            "status": self.status.value,
            "total_amount_moved": self.total_amount_moved,
            "total_amount_blocked": self.total_amount_blocked,
            "num_transactions": len(self.transactions),
            "detection_time": self.detection_time,
            "intervention_time": self.intervention_time,
            "total_attempted_amount": self.total_attempted_amount,
            "exposure_before_detection": self.exposure_before_detection,
            "exposure_before_intervention": self.exposure_before_intervention,
            "termination_reason": self.termination_reason,
            "is_fraud": self.is_fraud,
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
        attacker_id: Optional[str] = None,
        vpa_strategy: Optional[VPAStrategy] = None
    ) -> Campaign:
        """
        Create a known fraud campaign.

        Known fraud uses patterns similar to training data:
        - High transaction amounts (₹10,000-50,000 per attempt)
        - High velocity
        - New beneficiaries

        Default target: ₹30,000 (achievable in 1-3 successful transactions)
        Family: HIGH_VALUE_BURST
        Default VPA strategy: SINGLE_COMPROMISED_VPA
        """
        if target_amount is None:
            # Realistic target: 1-3 successful high-value transactions
            # Base transaction ≈ ₹25,000, so target of ₹30,000 is feasible
            target_amount = 30000

        if attacker_id is None:
            attacker_id = f"attacker_{uuid.uuid4().hex[:8]}"

        if vpa_strategy is None:
            # Default: compromised account model (matches training fraud)
            vpa_strategy = VPAStrategy.SINGLE_COMPROMISED_VPA

        campaign = Campaign(
            campaign_id=f"known_{uuid.uuid4().hex[:8]}",
            attacker_id=attacker_id,
            objective="Move funds using known fraud patterns",
            target_amount=target_amount,
            fraud_type="known",
            family=CampaignFamily.HIGH_VALUE_BURST,
            vpa_strategy=vpa_strategy
        )

        self.campaigns.append(campaign)
        return campaign

    def create_unknown_fraud_campaign(
        self,
        target_amount: float = None,
        attacker_id: Optional[str] = None,
        vpa_strategy: Optional[VPAStrategy] = None
    ) -> Campaign:
        """
        Create an unknown fraud campaign.

        Unknown fraud uses patterns different from training data.
        Randomly selects one of three unknown families:
        - SLOW_DRAIN: Small repeated transactions
        - GRADUAL_ESCALATION: Progressive amount increase
        - BENEFICIARY_HOPPING: Rapid beneficiary rotation

        Default target: ₹15,000 (achievable in multiple successful transactions)
        Family: Random selection from unknown families
        Default VPA strategy: MIXED_REUSE
        """
        import random

        if target_amount is None:
            target_amount = 15000

        if attacker_id is None:
            attacker_id = f"attacker_{uuid.uuid4().hex[:8]}"

        if vpa_strategy is None:
            # Default: mixed reuse (some source repetition, some diversity)
            vpa_strategy = VPAStrategy.MIXED_REUSE

        # Randomly select one of the three unknown families
        unknown_families = [
            CampaignFamily.SLOW_DRAIN,
            CampaignFamily.GRADUAL_ESCALATION,
            CampaignFamily.BENEFICIARY_HOPPING
        ]
        selected_family = random.choice(unknown_families)

        campaign = Campaign(
            campaign_id=f"unknown_{uuid.uuid4().hex[:8]}",
            attacker_id=attacker_id,
            objective="Move funds using previously unseen patterns",
            target_amount=target_amount,
            fraud_type="unknown",
            family=selected_family,
            vpa_strategy=vpa_strategy
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
