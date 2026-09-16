"""
Rule-based adaptive attacker.

Observes detector responses and adjusts strategy accordingly.
"""
from typing import Dict, List, Optional
import random
from enum import Enum


class AttackerAction(Enum):
    """Possible attacker actions."""
    INCREASE_AMOUNT = "INCREASE_AMOUNT"
    DECREASE_AMOUNT = "DECREASE_AMOUNT"
    CHANGE_TIMING = "CHANGE_TIMING"
    CHANGE_BENEFICIARY = "CHANGE_BENEFICIARY"
    CHANGE_PATH = "CHANGE_PATH"
    CONTINUE = "CONTINUE"
    STOP = "STOP"


class AdaptiveAttacker:
    """
    Rule-based adaptive attacker.

    Observes detector responses and changes strategy:
    - If BLOCKED → reduce amount or change beneficiary
    - If FLAGGED → moderate adjustment
    - If ALLOWED → continue or escalate
    """

    def __init__(self, fraud_type: str = "known"):
        """
        Initialize adaptive attacker.

        Args:
            fraud_type: "known" or "unknown"
        """
        self.fraud_type = fraud_type
        self.step = 0
        self.history = []

        # Adaptive parameters
        self.current_amount_multiplier = 1.0
        self.used_beneficiaries = set()
        self.blocked_count = 0
        self.flagged_count = 0
        self.allowed_count = 0

    def choose_action(
        self,
        campaign: 'Campaign',
        state: Dict,
        accounts: List[str]
    ) -> Optional[Dict]:
        """
        Choose next transaction based on adaptive strategy.

        Args:
            campaign: Current campaign
            state: Current environment state
            accounts: Available accounts

        Returns:
            Transaction dict or None if campaign should stop
        """
        self.step += 1

        # Stop if too many blocks
        if self.blocked_count >= 3:
            return None

        # Determine base amount based on fraud type and history
        if self.fraud_type == "known":
            base_amount = 25000
        else:
            base_amount = 3000

        # Adjust based on recent responses
        amount = base_amount * self.current_amount_multiplier

        # Add some randomness
        amount = amount * random.uniform(0.9, 1.1)

        # Pick accounts
        from_account = random.choice(accounts)

        # Try to use a fresh beneficiary if recent transactions were blocked
        available_beneficiaries = [
            a for a in accounts
            if a != from_account and a not in self.used_beneficiaries
        ]

        if available_beneficiaries and self.blocked_count > 0:
            to_account = random.choice(available_beneficiaries)
        else:
            to_account = random.choice([a for a in accounts if a != from_account])

        self.used_beneficiaries.add(to_account)

        transaction = {
            "from_vpa": from_account,
            "to_vpa": to_account,
            "amount": round(amount, 2),
            "campaign_id": campaign.campaign_id,
            "step": self.step
        }

        return transaction

    def observe(self, response: Dict):
        """
        Observe detector response and adapt strategy.

        Args:
            response: Detector response with decision and risk_score
        """
        self.history.append(response)
        decision = response.get("decision", "UNKNOWN")
        risk_score = response.get("risk_score", 0.5)

        if decision == "BLOCK":
            self.blocked_count += 1

            # Strong negative feedback - reduce amount significantly
            self.current_amount_multiplier *= 0.5

            # Reset beneficiary pool to try different accounts
            if len(self.used_beneficiaries) > 3:
                self.used_beneficiaries.clear()

        elif decision == "FLAG":
            self.flagged_count += 1

            # Moderate negative feedback - small reduction
            self.current_amount_multiplier *= 0.8

        elif decision == "ALLOW":
            self.allowed_count += 1

            # Positive feedback - can try to escalate slightly
            # But not too aggressively
            self.current_amount_multiplier = min(
                self.current_amount_multiplier * 1.1,
                2.0  # Cap at 2x base amount
            )

        # Ensure multiplier doesn't go too low
        self.current_amount_multiplier = max(
            self.current_amount_multiplier,
            0.2  # Floor at 0.2x base amount
        )

    def get_adaptation_summary(self) -> Dict:
        """Get summary of adaptive behavior."""
        return {
            "steps": self.step,
            "blocked_count": self.blocked_count,
            "flagged_count": self.flagged_count,
            "allowed_count": self.allowed_count,
            "amount_multiplier": self.current_amount_multiplier,
            "unique_beneficiaries": len(self.used_beneficiaries)
        }
