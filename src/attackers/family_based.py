"""
Family-based attackers that implement campaign-specific behavioral mechanisms.

Each attacker family executes a DISTINCT fraud mechanism:
- GradualEscalationAttacker: starts small, increases systematically
- BeneficiaryHoppingAttacker: rotates beneficiaries rapidly
"""
from typing import Dict, List, Optional
import random
from enum import Enum


class GradualEscalationAttacker:
    """
    Gradual escalation attacker.

    Behavioral mechanism:
    - Start with very small amounts (₹500-1,000)
    - After each successful transaction, increase amount
    - If blocked, reduce slightly and retry
    - Systematically probes detector boundaries

    This differs from training fraud which typically starts high.
    """

    def __init__(self, fraud_type: str = "unknown"):
        self.fraud_type = fraud_type
        self.step = 0
        self.history = []

        # Escalation state
        self.current_amount = 500  # Start very small
        self.min_amount = 500
        self.max_amount = 25000
        self.escalation_factor = 1.3  # Increase by 30% on success
        self.blocked_count = 0
        self.allowed_count = 0

    def choose_action(
        self,
        campaign: 'Campaign',
        state: Dict,
        accounts: List[str]
    ) -> Optional[Dict]:
        """
        Choose next transaction with gradual escalation.
        """
        self.step += 1

        # Stop if too many consecutive blocks
        if self.blocked_count >= 5:
            return None

        # Pick accounts
        from_account = random.choice(accounts)
        to_account = random.choice([a for a in accounts if a != from_account])

        # Add small randomness to current amount
        amount = self.current_amount * random.uniform(0.95, 1.05)
        amount = max(self.min_amount, min(amount, self.max_amount))

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
        Observe response and adjust escalation strategy.
        """
        self.history.append(response)
        decision = response.get("decision", "UNKNOWN")

        if decision == "BLOCK":
            self.blocked_count += 1
            # Blocked - reduce amount and try smaller
            self.current_amount *= 0.7
            self.current_amount = max(self.min_amount, self.current_amount)

        elif decision == "FLAG":
            # Flagged but went through - maintain current level
            self.current_amount *= 0.95

        elif decision == "ALLOW":
            self.blocked_count = 0  # Reset block counter
            self.allowed_count += 1
            # Success - escalate gradually
            self.current_amount *= self.escalation_factor
            self.current_amount = min(self.max_amount, self.current_amount)

    def get_adaptation_summary(self) -> Dict:
        """Get summary of escalation behavior."""
        return {
            "steps": self.step,
            "blocked_count": self.blocked_count,
            "allowed_count": self.allowed_count,
            "current_amount": self.current_amount,
            "escalation_factor": self.escalation_factor
        }


class BeneficiaryHoppingAttacker:
    """
    Beneficiary hopping attacker.

    Behavioral mechanism:
    - Rapidly rotate through many different beneficiaries
    - Use each beneficiary only once or twice
    - Keeps amounts moderate to avoid single-transaction detection
    - Exploits potential blind spot: per-VPA velocity vs global behavior

    This differs from training fraud which may reuse beneficiaries.
    """

    def __init__(self, fraud_type: str = "unknown"):
        self.fraud_type = fraud_type
        self.step = 0
        self.history = []

        # Hopping state
        self.beneficiary_use_count = {}  # Track uses per beneficiary
        self.max_uses_per_beneficiary = 2
        self.blocked_count = 0
        self.base_amount = 3000 if fraud_type == "unknown" else 15000

    def choose_action(
        self,
        campaign: 'Campaign',
        state: Dict,
        accounts: List[str]
    ) -> Optional[Dict]:
        """
        Choose next transaction with beneficiary hopping.
        """
        self.step += 1

        # Stop if too many blocks
        if self.blocked_count >= 5:
            return None

        # Pick from account
        from_account = random.choice(accounts)

        # Pick FRESH beneficiary (minimize reuse)
        unused_beneficiaries = [
            a for a in accounts
            if a != from_account and self.beneficiary_use_count.get(a, 0) < self.max_uses_per_beneficiary
        ]

        if not unused_beneficiaries:
            # All beneficiaries exhausted - reset or stop
            self.beneficiary_use_count.clear()
            unused_beneficiaries = [a for a in accounts if a != from_account]

        to_account = random.choice(unused_beneficiaries)
        self.beneficiary_use_count[to_account] = self.beneficiary_use_count.get(to_account, 0) + 1

        # Moderate amounts with variation
        amount = self.base_amount * random.uniform(0.8, 1.2)

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
        Observe response and adjust hopping strategy.
        """
        self.history.append(response)
        decision = response.get("decision", "UNKNOWN")

        if decision == "BLOCK":
            self.blocked_count += 1
            # Reduce amount slightly if blocked
            self.base_amount *= 0.9

        elif decision == "ALLOW":
            self.blocked_count = 0  # Reset
            # Can slightly increase if successful
            self.base_amount *= 1.05

        # Keep base amount in reasonable range
        self.base_amount = max(1000, min(20000, self.base_amount))

    def get_adaptation_summary(self) -> Dict:
        """Get summary of hopping behavior."""
        return {
            "steps": self.step,
            "blocked_count": self.blocked_count,
            "unique_beneficiaries": len(self.beneficiary_use_count),
            "base_amount": self.base_amount
        }
