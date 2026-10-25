"""
Campaign executor - runs the attacker-detector loop.
"""
import random
import math
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime

from src.campaigns.timing import CampaignTimer
from src.campaigns.vpa_strategy import VPASelector, VPAStrategy
from src.campaigns.generator import CampaignStatus
from src.experiments.config import derive_seed


@dataclass(frozen=True)
class AttackerCampaignView:
    """Own declared objective only; never internal outcomes or detector state."""
    campaign_id: str
    target_amount: float
    family: object
    fraud_type: str


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
        max_steps: int = 50,
        feedback: str = "label_only",
        max_transaction_amount: float = 50000,
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
        if max_steps <= 0 or feedback not in ("label_only", "score"):
            raise ValueError("Invalid executor configuration")
        self.feedback, self.max_transaction_amount = feedback, max_transaction_amount

    def execute_campaign(
        self,
        campaign: 'Campaign',
        accounts: List[str],
        verbose: bool = False,
        seed: Optional[int] = None
    ) -> 'Campaign':
        """
        Execute a fraud campaign.

        Args:
            campaign: Campaign to execute
            accounts: Available accounts for transactions
            verbose: Print step-by-step output
            seed: Random seed for reproducible timing and VPA selection

        Returns:
            Completed campaign
        """
        seed = 42 if seed is None else seed
        if hasattr(self.attacker, "random"):
            self.attacker.random = random.Random(getattr(campaign, "policy_seed",
                                                         derive_seed(seed, "policy")))
        # Initialize timer based on campaign family
        if campaign.family:
            timer = CampaignTimer(
                family=campaign.family,
                start_time=campaign.created_at,
                seed=getattr(campaign, "timer_seed", derive_seed(seed, "timer"))
            )
            # Attach timer to attacker so it can generate timestamps
            self.attacker.timer = timer
        else:
            # No timing model - transactions use datetime.now()
            self.attacker.timer = None

        # Initialize VPA selector based on campaign strategy
        if campaign.vpa_strategy:
            vpa_selector = VPASelector(
                strategy=campaign.vpa_strategy,
                available_vpas=accounts,
                seed=getattr(campaign, "vpa_seed", derive_seed(seed, "vpa"))
            )
            # Attach VPA selector to attacker
            self.attacker.vpa_selector = vpa_selector
        else:
            # No VPA strategy - attacker uses random selection
            self.attacker.vpa_selector = None

        step = 0
        last_time = campaign.created_at
        view = AttackerCampaignView(campaign.campaign_id, campaign.target_amount,
                                    campaign.family, campaign.fraud_type)
        if len(set(accounts)) < 2:
            raise ValueError("At least two controlled VPAs required")
        if hasattr(self.attacker, "begin_episode"):
            self.attacker.begin_episode(view, self.max_steps)

        if verbose:
            print(f"\n{'='*60}")
            print(f"CAMPAIGN: {campaign.campaign_id}")
            print(f"Type: {campaign.fraud_type}")
            print(f"Family: {campaign.family.value if campaign.family else 'N/A'}")
            print(f"VPA Strategy: {campaign.vpa_strategy.value if campaign.vpa_strategy else 'N/A'}")
            print(f"Target: ₹{campaign.target_amount:,.2f}")
            if campaign.family:
                print(f"Timing: {timer.get_description()}")
            if campaign.vpa_strategy:
                print(f"Source VPA: {vpa_selector.get_strategy_description()}")
            print(f"{'='*60}\n")

        campaign.proposals = 0
        while step < self.max_steps and not campaign.is_complete():
            step += 1

            # Attacker chooses next transaction
            transaction = self.attacker.choose_action(
                view,
                state={},  # Could include environment state
                accounts=accounts
            )

            if transaction is None:
                # Attacker decided to stop
                campaign.finalize(CampaignStatus.FAILED, "attacker_stopped", last_time)
                break
            campaign.proposals += 1

            # Ensure timestamp is present (attacker should provide it)
            if 'timestamp' not in transaction:
                # Fallback: use current time if attacker didn't provide timestamp
                transaction['timestamp'] = last_time.isoformat()

            try:
                when = transaction["timestamp"]
                if isinstance(when, str):
                    when = datetime.fromisoformat(when)
                amount = transaction["amount"]
                if (not isinstance(when, datetime) or when.tzinfo is not None
                        or when < last_time
                        or transaction["from_vpa"] not in accounts
                        or transaction["to_vpa"] not in accounts
                        or transaction["from_vpa"] == transaction["to_vpa"]
                        or not math.isfinite(amount) or amount <= 0
                        or amount > self.max_transaction_amount):
                    raise ValueError("Action violates declared threat model")
                if amount > campaign.budget - campaign.total_amount_moved:
                    campaign.finalize(CampaignStatus.FAILED, "budget_exhausted", last_time)
                    break
                if (when - campaign.created_at).total_seconds() > campaign.max_duration_seconds:
                    campaign.finalize(CampaignStatus.TIMED_OUT, "time_horizon", last_time)
                    break
            except (KeyError, ValueError, TypeError) as exc:
                campaign.finalize(CampaignStatus.INVALID, "invalid_action", last_time)
                campaign.invalid_action = {"step": step, "reason": str(exc)}
                break
            transaction["timestamp"] = when.isoformat()
            transaction["transaction_id"] = f"{campaign.campaign_id}-step-{step:04d}"

            # Environment evaluates and decides (uses its internal detector)
            response = self.environment.process_transaction(transaction)
            if response["execution_status"] == "invalid":
                campaign.finalize(CampaignStatus.INVALID, "infeasible_execution", when)
                campaign.invalid_action = {"step": step, "reason": response.get("details")}
                break

            # Add response details to transaction
            transaction.update(response)

            # Campaign records transaction
            campaign.add_transaction(transaction)

            # Attacker observes response and adapts
            public_keys = ("from_vpa", "to_vpa", "amount", "timestamp", "decision",
                           "amount_transferred", "execution_status", "status")
            feedback = {key: response[key] for key in public_keys}
            if self.feedback == "score":
                feedback["risk_score"] = response["risk_score"]
            self.attacker.observe(feedback)
            if hasattr(self.attacker, "last_transition"):
                transaction["rl_transition"] = self.attacker.last_transition
            last_time = when

            if verbose:
                self._print_step(step, transaction, response)

        if not campaign.is_complete():
            campaign.finalize(CampaignStatus.TIMED_OUT, "step_horizon", last_time)
        if hasattr(self.attacker, "end_episode"):
            self.attacker.end_episode(campaign.status.value)

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
            print(f"  Attacker state: {summary}")

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
