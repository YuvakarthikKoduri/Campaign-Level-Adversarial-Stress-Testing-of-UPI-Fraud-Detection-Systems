"""
UPI Environment Simulator

Simulates a UPI transaction environment with:
- Account and VPA management
- Transaction processing with fraud detection integration
- Sequential transaction support
- Risk-based decision making (ALLOW/FLAG/BLOCK)
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

from .entities import Account, VPA, Transaction
from .thresholds import ThresholdConfig, RiskDecision, get_default_thresholds


logger = logging.getLogger(__name__)


class UPIEnvironment:
    """
    UPI transaction environment simulator

    Manages accounts, VPAs, and processes transactions with integrated
    fraud detection and risk-based decision making.
    """

    def __init__(
        self,
        threshold_config: Optional[ThresholdConfig] = None,
        fraud_detector = None
    ):
        """
        Initialize UPI environment

        Args:
            threshold_config: Risk threshold configuration
            fraud_detector: Fraud detection model/system (optional)
        """
        self.accounts: Dict[str, Account] = {}
        self.vpas: Dict[str, VPA] = {}
        self.transactions: List[Transaction] = []

        self.threshold_config = threshold_config or get_default_thresholds()
        self.fraud_detector = fraud_detector

        # Statistics
        self.stats = {
            "total_transactions": 0,
            "allowed": 0,
            "flagged": 0,
            "blocked": 0,
            "failed": 0
        }

        logger.info("UPI Environment initialized")

    def create_account(
        self,
        account_id: str,
        initial_balance: float = 10000.0,
        account_type: str = "savings"
    ) -> Account:
        """
        Create a new bank account

        Args:
            account_id: Unique account identifier
            initial_balance: Starting balance
            account_type: Account type (savings/current)

        Returns:
            Created Account object
        """
        if account_id in self.accounts:
            raise ValueError(f"Account {account_id} already exists")

        account = Account(
            account_id=account_id,
            balance=initial_balance,
            account_type=account_type
        )
        self.accounts[account_id] = account
        logger.info(f"Created account {account_id} with balance {initial_balance}")
        return account

    def create_vpa(
        self,
        vpa_id: str,
        account_id: str,
        name: str,
        vpa_type: str = "individual"
    ) -> VPA:
        """
        Create a new VPA linked to an account

        Args:
            vpa_id: VPA identifier (e.g., "user@paytm")
            account_id: Associated account ID
            name: Account holder name
            vpa_type: VPA type (individual/merchant)

        Returns:
            Created VPA object
        """
        if vpa_id in self.vpas:
            raise ValueError(f"VPA {vpa_id} already exists")

        if account_id not in self.accounts:
            raise ValueError(f"Account {account_id} does not exist")

        vpa = VPA(
            vpa_id=vpa_id,
            account_id=account_id,
            name=name,
            vpa_type=vpa_type
        )
        self.vpas[vpa_id] = vpa
        logger.info(f"Created VPA {vpa_id} for account {account_id}")
        return vpa

    def get_account_by_vpa(self, vpa_id: str) -> Optional[Account]:
        """Get account associated with a VPA"""
        vpa = self.vpas.get(vpa_id)
        if vpa:
            return self.accounts.get(vpa.account_id)
        return None

    def _calculate_risk_score(self, transaction: Transaction) -> Tuple[float, List[str]]:
        """
        Calculate risk score for a transaction

        Args:
            transaction: Transaction to assess

        Returns:
            Tuple of (risk_score, risk_factors)
        """
        if self.fraud_detector is None:
            # Default: basic rule-based risk assessment
            risk_score = 0.0
            risk_factors = []

            # High amount transactions
            if transaction.amount > 50000:
                risk_score += 0.3
                risk_factors.append("high_amount")

            # Check sender account balance
            sender_account = self.get_account_by_vpa(transaction.from_vpa)
            if sender_account and transaction.amount > sender_account.balance * 0.8:
                risk_score += 0.2
                risk_factors.append("high_balance_ratio")

            # Cap at 1.0
            risk_score = min(risk_score, 1.0)

            return risk_score, risk_factors
        else:
            # Use provided fraud detector
            # Prepare features for the model
            try:
                # Compute UPI features from transaction context
                features = self._compute_upi_features(transaction)

                # Store features in transaction for debugging
                for key, value in features.items():
                    transaction.add_feature(key, value)

                result = self.fraud_detector.predict(features)
                if isinstance(result, tuple):
                    return result
                else:
                    return float(result), []
            except Exception as e:
                logger.error(f"Fraud detector error: {e}")
                return 0.5, ["detector_error"]

    def _compute_upi_features(self, transaction: Transaction) -> Dict:
        """
        Compute UPI-specific features for fraud detection.

        Args:
            transaction: Transaction to compute features for

        Returns:
            Dictionary with features: amount, hour_of_day, velocity_1h, is_new_vpa
        """
        # Get basic features
        amount = transaction.amount
        hour_of_day = transaction.timestamp.hour

        # Compute velocity (transactions in last hour from this VPA)
        one_hour_ago = transaction.timestamp.timestamp() - 3600
        recent_from_vpa = [
            t for t in self.transactions
            if t.from_vpa == transaction.from_vpa
            and t.timestamp.timestamp() > one_hour_ago
        ]
        velocity_1h = len(recent_from_vpa)

        # Check if VPA is new (not in our registered VPAs)
        is_new_vpa = 0
        if transaction.from_vpa not in self.vpas:
            is_new_vpa = 1

        return {
            "amount": amount,
            "hour_of_day": hour_of_day,
            "velocity_1h": velocity_1h,
            "is_new_vpa": is_new_vpa
        }

    def process_transaction(self, transaction_data: Dict) -> Dict:
        """
        Process a UPI transaction with fraud detection

        Args:
            transaction_data: Dictionary containing transaction details:
                - from_vpa: Sender VPA
                - to_vpa: Receiver VPA
                - amount: Transaction amount
                - timestamp (optional): Transaction timestamp
                - features (optional): Additional features for detection

        Returns:
            Dictionary with:
                - transaction_id: Unique transaction ID
                - risk_score: Calculated risk score
                - decision: ALLOW, FLAG, or BLOCK
                - status: Transaction status
                - details: Additional information
        """
        # Create transaction object
        try:
            transaction = Transaction.from_dict(transaction_data)
        except Exception as e:
            logger.error(f"Invalid transaction data: {e}")
            return {
                "transaction_id": None,
                "risk_score": None,
                "decision": "BLOCK",
                "status": "failed",
                "details": f"Invalid transaction data: {str(e)}"
            }

        # Auto-register unknown VPAs so campaigns work without manual setup
        for vpa_id in [transaction.from_vpa, transaction.to_vpa]:
            if vpa_id not in self.vpas:
                acct_id = f"acct_{vpa_id.replace('@', '_').replace('.', '_')}"
                if acct_id not in self.accounts:
                    self.create_account(acct_id, initial_balance=500000.0)
                self.create_vpa(vpa_id, acct_id, vpa_id)

        # Get accounts
        sender_account = self.get_account_by_vpa(transaction.from_vpa)
        receiver_account = self.get_account_by_vpa(transaction.to_vpa)

        if not sender_account or not receiver_account:
            return {
                "transaction_id": transaction.transaction_id,
                "risk_score": None,
                "decision": "BLOCK",
                "status": "failed",
                "details": "Account not found"
            }

        # Check sender balance
        if sender_account.balance < transaction.amount:
            transaction.mark_status("failed")
            self.transactions.append(transaction)
            self.stats["failed"] += 1
            return {
                "transaction_id": transaction.transaction_id,
                "risk_score": None,
                "decision": "BLOCK",
                "status": "failed",
                "details": "Insufficient balance"
            }

        # Calculate risk score
        risk_score, risk_factors = self._calculate_risk_score(transaction)
        transaction.update_risk_score(risk_score, risk_factors)

        # Get decision based on threshold
        decision = self.threshold_config.get_decision(risk_score)

        # Process based on decision
        if decision == RiskDecision.BLOCK:
            transaction.mark_status("blocked")
            self.transactions.append(transaction)
            self.stats["total_transactions"] += 1
            self.stats["blocked"] += 1

            return {
                "transaction_id": transaction.transaction_id,
                "risk_score": risk_score,
                "decision": decision.value,
                "status": "blocked",
                "details": f"Transaction blocked due to high risk. Factors: {risk_factors}",
                "features": transaction.features  # Include computed features
            }

        elif decision == RiskDecision.FLAG:
            # Process transaction but flag it
            if sender_account.debit(transaction.amount, transaction.transaction_id):
                receiver_account.credit(transaction.amount, transaction.transaction_id)
                transaction.mark_status("flagged")
                self.transactions.append(transaction)
                self.stats["total_transactions"] += 1
                self.stats["flagged"] += 1

                return {
                    "transaction_id": transaction.transaction_id,
                    "risk_score": risk_score,
                    "decision": decision.value,
                    "status": "success",
                    "details": f"Transaction flagged for review. Factors: {risk_factors}",
                    "features": transaction.features  # Include computed features
                }

        else:  # ALLOW
            # Process transaction normally
            if sender_account.debit(transaction.amount, transaction.transaction_id):
                receiver_account.credit(transaction.amount, transaction.transaction_id)
                transaction.mark_status("success")
                self.transactions.append(transaction)
                self.stats["total_transactions"] += 1
                self.stats["allowed"] += 1

                return {
                    "transaction_id": transaction.transaction_id,
                    "risk_score": risk_score,
                    "decision": decision.value,
                    "status": "success",
                    "details": "Transaction processed successfully",
                    "features": transaction.features  # Include computed features
                }

        # Should not reach here
        return {
            "transaction_id": transaction.transaction_id,
            "risk_score": risk_score,
            "decision": "BLOCK",
            "status": "failed",
            "details": "Unexpected error"
        }

    def get_account_balance(self, vpa_id: str) -> Optional[float]:
        """Get account balance by VPA"""
        account = self.get_account_by_vpa(vpa_id)
        return account.balance if account else None

    def get_transaction_history(
        self,
        vpa_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get transaction history

        Args:
            vpa_id: Filter by VPA (optional)
            limit: Maximum number of transactions to return

        Returns:
            List of transaction dictionaries
        """
        transactions = self.transactions[-limit:]

        if vpa_id:
            transactions = [
                t for t in transactions
                if t.from_vpa == vpa_id or t.to_vpa == vpa_id
            ]

        return [t.to_dict() for t in transactions]

    def get_statistics(self) -> Dict:
        """Get environment statistics"""
        return {
            **self.stats,
            "accounts": len(self.accounts),
            "vpas": len(self.vpas),
            "total_balance": sum(acc.balance for acc in self.accounts.values()),
            "thresholds": self.threshold_config.to_dict()
        }

    def reset_statistics(self) -> None:
        """Reset transaction statistics"""
        self.stats = {
            "total_transactions": 0,
            "allowed": 0,
            "flagged": 0,
            "blocked": 0,
            "failed": 0
        }

    def update_thresholds(
        self,
        flag_threshold: float = None,
        block_threshold: float = None
    ) -> None:
        """Update risk thresholds"""
        self.threshold_config.update_thresholds(flag_threshold, block_threshold)
        logger.info(f"Updated thresholds: {self.threshold_config.to_dict()}")
