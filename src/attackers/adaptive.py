"""
Enhanced stateful adaptive attacker.

Observes detector responses and learns:
- Tracks safe regions (successful transaction parameters)
- Adapts across multiple dimensions: amount, timing, velocity
- Exploits discovered vulnerabilities
- Strategic probing of detector boundaries
"""
from typing import Dict, List, Optional, Tuple
import random
from enum import Enum
from datetime import datetime


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
    Enhanced stateful adaptive attacker.

    Learns from detector responses:
    - Tracks safe regions (amount ranges that succeeded)
    - Remembers successful transaction patterns
    - Adapts amount, timing, and beneficiary strategy
    - Exploits discovered blind spots
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
        self.timer = None  # Set by campaign execution
        self.vpa_selector = None  # Set by campaign execution

        # Adaptive parameters
        self.current_amount_multiplier = 1.0
        self.used_beneficiaries = set()
        self.blocked_count = 0
        self.flagged_count = 0
        self.allowed_count = 0

        # ENHANCED: Track safe regions learned from successful transactions
        self.safe_amounts = []  # Amounts that were allowed
        self.safe_beneficiaries = set()  # Beneficiaries that worked
        self.consecutive_blocks = 0
        self.adaptation_count = 0  # Number of strategy changes

        # Strategic state
        self.probing_mode = False  # Whether actively testing boundaries
        self.exploit_mode = False  # Whether exploiting known safe region

    def choose_action(
        self,
        campaign: 'Campaign',
        state: Dict,
        accounts: List[str]
    ) -> Optional[Dict]:
        """
        Choose next transaction based on adaptive strategy.

        Strategy:
        1. If safe region known → exploit it
        2. If consecutive blocks → probe with smaller amounts
        3. Otherwise → adapt based on recent feedback

        Args:
            campaign: Current campaign
            state: Current environment state
            accounts: Available accounts

        Returns:
            Transaction dict or None if campaign should stop
        """
        self.step += 1

        # Stop if too many consecutive blocks without progress
        if self.consecutive_blocks >= 5:
            return None

        # Determine base amount based on fraud type
        if self.fraud_type == "known":
            base_amount = 25000
        else:
            base_amount = 3000

        # ENHANCED: Exploit safe region if discovered
        if self.safe_amounts and random.random() < 0.6:  # 60% chance to exploit
            # Use known-safe amount range
            self.exploit_mode = True
            safe_mean = sum(self.safe_amounts) / len(self.safe_amounts)
            safe_std = max(500, safe_mean * 0.15)  # 15% variation
            amount = random.gauss(safe_mean, safe_std)
            amount = max(500, amount)  # Floor at ₹500
        else:
            # Regular adaptive strategy
            self.exploit_mode = False
            amount = base_amount * self.current_amount_multiplier
            amount = amount * random.uniform(0.9, 1.1)

        # ENHANCED: Strategic beneficiary selection
        # Use VPA selector for source if available, otherwise random
        if self.vpa_selector:
            from_account = self.vpa_selector.select_source_vpa()
        else:
            from_account = random.choice(accounts)

        if self.safe_beneficiaries and random.random() < 0.4:
            # Sometimes reuse beneficiaries that worked
            available_safe = [b for b in self.safe_beneficiaries if b != from_account]
            if available_safe:
                to_account = random.choice(available_safe)
            else:
                to_account = self._choose_fresh_beneficiary(accounts, from_account)
        else:
            # Use fresh beneficiary
            to_account = self._choose_fresh_beneficiary(accounts, from_account)

        transaction = {
            "from_vpa": from_account,
            "to_vpa": to_account,
            "amount": round(amount, 2),
            "campaign_id": campaign.campaign_id,
            "step": self.step
        }

        # Add timestamp if timer is available
        if self.timer:
            transaction["timestamp"] = self.timer.next_transaction_time()

        return transaction

    def _choose_fresh_beneficiary(self, accounts: List[str], from_account: str) -> str:
        """Choose a fresh beneficiary, preferring unused ones."""
        available_fresh = [
            a for a in accounts
            if a != from_account and a not in self.used_beneficiaries
        ]

        if available_fresh and (self.blocked_count > 0 or random.random() < 0.7):
            beneficiary = random.choice(available_fresh)
        else:
            beneficiary = random.choice([a for a in accounts if a != from_account])

        self.used_beneficiaries.add(beneficiary)
        return beneficiary

    def observe(self, response: Dict):
        """
        Observe detector response and adapt strategy.

        ENHANCED: Learns safe regions and exploits blind spots.

        Args:
            response: Detector response with decision and risk_score
        """
        self.history.append(response)
        decision = response.get("decision", "UNKNOWN")
        risk_score = response.get("risk_score", 0.5)
        amount = response.get("amount", 0)

        if decision == "BLOCK":
            self.blocked_count += 1
            self.consecutive_blocks += 1

            # Strong negative feedback - reduce amount significantly
            self.current_amount_multiplier *= 0.5
            self.adaptation_count += 1

            # Reset beneficiary pool to try different accounts
            if len(self.used_beneficiaries) > 3:
                self.used_beneficiaries.clear()

        elif decision == "FLAG":
            self.flagged_count += 1
            self.consecutive_blocks = 0  # Reset counter

            # Moderate negative feedback - small reduction
            self.current_amount_multiplier *= 0.8
            self.adaptation_count += 1

            # ENHANCED: Still went through - remember as borderline safe
            if amount > 0 and len(self.safe_amounts) < 10:
                self.safe_amounts.append(amount * 0.9)  # Slightly below flagged

        elif decision == "ALLOW":
            self.allowed_count += 1
            self.consecutive_blocks = 0  # Reset counter

            # ENHANCED: Learn safe region
            if amount > 0:
                self.safe_amounts.append(amount)
                # Keep only recent safe amounts (last 15)
                if len(self.safe_amounts) > 15:
                    self.safe_amounts = self.safe_amounts[-15:]

                # Track safe beneficiary
                to_vpa = response.get("to_vpa")
                if to_vpa:
                    self.safe_beneficiaries.add(to_vpa)

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
        safe_amount_range = None
        if self.safe_amounts:
            safe_amount_range = (min(self.safe_amounts), max(self.safe_amounts))

        return {
            "steps": self.step,
            "blocked_count": self.blocked_count,
            "flagged_count": self.flagged_count,
            "allowed_count": self.allowed_count,
            "amount_multiplier": self.current_amount_multiplier,
            "unique_beneficiaries": len(self.used_beneficiaries),
            "adaptation_count": self.adaptation_count,
            "safe_amounts_learned": len(self.safe_amounts),
            "safe_amount_range": safe_amount_range,
            "safe_beneficiaries": len(self.safe_beneficiaries),
            "exploit_mode": self.exploit_mode
        }
