"""
Static attacker - follows a fixed strategy.

Does not adapt to detector responses.
"""
from typing import Dict, List, Optional
from datetime import datetime
import random


class StaticAttacker:
    """
    Static attacker that follows a predefined strategy.

    Does not react to detector feedback.
    """

    def __init__(self, fraud_type: str = "known", seed=None):
        """
        Initialize static attacker.

        Args:
            fraud_type: "known" or "unknown"
        """
        self.fraud_type = fraud_type
        self.random = random.Random(seed)
        self.step = 0
        self.timer = None  # Set by campaign execution
        self.vpa_selector = None  # Set by campaign execution

    def choose_action(
        self,
        campaign: 'Campaign',
        state: Dict,
        accounts: List[str]
    ) -> Optional[Dict]:
        """
        Choose next transaction.

        Args:
            campaign: Current campaign
            state: Current environment state
            accounts: Available accounts

        Returns:
            Transaction dict or None if campaign should stop
        """
        self.step += 1

        # Simple strategy based on fraud type
        if self.fraud_type == "known":
            return self._known_fraud_transaction(campaign, accounts)
        else:
            return self._unknown_fraud_transaction(campaign, accounts)

    def _known_fraud_transaction(
        self,
        campaign: 'Campaign',
        accounts: List[str]
    ) -> Dict:
        """
        Generate a known fraud transaction.

        Known fraud characteristics:
        - High amounts (₹10,000 - ₹50,000)
        - Fast succession
        - Direct transfers
        """
        amount = self.random.uniform(10000, 50000)

        # Use VPA selector if available, otherwise random
        if self.vpa_selector:
            from_account = self.vpa_selector.select_source_vpa()
        else:
            from_account = self.random.choice(accounts)

        to_account = self.random.choice([a for a in accounts if a != from_account])

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

    def _unknown_fraud_transaction(
        self,
        campaign: 'Campaign',
        accounts: List[str]
    ) -> Dict:
        """
        Generate an unknown fraud transaction.

        Unknown fraud characteristics:
        - Small amounts (₹1,000 - ₹5,000)
        - Gradual movement
        - Multiple hops
        """
        amount = self.random.uniform(1000, 5000)

        # Use VPA selector if available, otherwise random
        if self.vpa_selector:
            from_account = self.vpa_selector.select_source_vpa()
        else:
            from_account = self.random.choice(accounts)

        to_account = self.random.choice([a for a in accounts if a != from_account])

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

    def observe(self, response: Dict):
        """
        Observe detector response.

        Static attacker does not react, so this is a no-op.
        """
        pass
