"""
Campaign executor - runs the attacker-detector loop.
"""
import time
from typing import Dict, List, Optional
from datetime import datetime


class CampaignExecutor:
    """
    Executes a fraud campaign with attacker-detector interaction.

    This is the core loop:
    1. Attacker chooses transaction
    2. Detector evaluates transaction
    3. Environment processes transaction
    4. Attacker observes response
    5. Repeat until campaign completes
    """

    def __init__(
        self,
        detector,
        environment,
        attacker,
        max_steps: int = 50
    ):
        """
        Initialize campaign executor.

        Args:
            detector: Fraud detector instance
            environment: UPI environment instance
            attacker: Attacker instance (static or adaptive)
            max_steps: Maximum transaction attempts
        """
        self.detector = detector
        self.environment = environment
        self.attacker = attacker
        self.max_steps = max_steps

    def execute_campaign(
        self,
        campaign: 'Campaign',
        accounts: List[str],
        verbose: bool = False
    ) -> 'Campaign':
        """
        Execute a fraud campaign.

        Args:
            campaign: Campaign to execute
            accounts: Available accounts for transactions
            verbose: Print step-by-step output

        Returns:
            Completed campaign
        """
        step = 0

        if verbose:
            print(f"\n{'='*60}")
            print(f"CAMPAIGN: {campaign.campaign_id}")
            print(f"Type: {campaign.fraud_type}")
            print(f"Target: ₹{campaign.target_amount:,.2f}")
            print(f"{'='*60}\n")

        while step < self.max_steps and not campaign.is_complete():
            step += 1

            # Attacker chooses next transaction
            transaction = self.attacker.choose_action(
                campaign,
                state={},  # Could include environment state
                accounts=accounts
            )

            if transaction is None:
                # Attacker decided to stop
                campaign.status = campaign.status  # Keep current status
                break

            # Add timestamp
            transaction['timestamp'] = datetime.now().isoformat()

            # Environment evaluates and decides (uses its internal detector)
            response = self.environment.process_transaction(transaction)

            # Add response details to transaction
            transaction.update(response)

            # Campaign records transaction
            campaign.add_transaction(transaction)

            # Attacker observes response and adapts
            self.attacker.observe(response)

            if verbose:
                self._print_step(step, transaction, response)

            # Small delay for realistic timing
            time.sleep(0.01)

        if verbose:
            self._print_summary(campaign)

        return campaign

    def _print_step(self, step: int, transaction: Dict, response: Dict):
        """Print step details."""
        print(f"Step {step}")
        print(f"  {transaction['from_vpa']} → {transaction['to_vpa']}")
        print(f"  Amount: ₹{transaction['amount']:,.2f}")
        print(f"  Risk: {response['risk_score']:.2f}")
        print(f"  Decision: {response['decision']}")

        if hasattr(self.attacker, 'get_adaptation_summary'):
            summary = self.attacker.get_adaptation_summary()
            print(f"  Attacker multiplier: {summary['amount_multiplier']:.2f}x")

        print()

    def _print_summary(self, campaign: 'Campaign'):
        """Print campaign summary."""
        print(f"{'='*60}")
        print(f"CAMPAIGN COMPLETE")
        print(f"Status: {campaign.status.value}")
        print(f"Amount moved: ₹{campaign.total_amount_moved:,.2f}")
        print(f"Amount blocked: ₹{campaign.total_amount_blocked:,.2f}")
        print(f"Transactions: {len(campaign.transactions)}")

        if campaign.detection_time:
            print(f"Detection time: {campaign.detection_time:.2f}s")
        if campaign.intervention_time:
            print(f"Intervention time: {campaign.intervention_time:.2f}s")

        print(f"{'='*60}\n")
