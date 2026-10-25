"""
UPI Transaction Environment Entities

Defines core entities for the UPI transaction simulation:
- Account: Represents a bank account with balance and history
- VPA: Virtual Payment Address linked to an account
- Transaction: Individual UPI transaction with metadata
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
import uuid
import math


@dataclass
class Account:
    """Bank account entity with balance tracking and transaction history"""

    account_id: str
    balance: float
    creation_date: datetime = field(default_factory=datetime.now)
    transaction_history: List[str] = field(default_factory=list)
    is_active: bool = True
    account_type: str = "savings"  # savings, current

    def __post_init__(self):
        """Validate account creation"""
        if self.balance < 0:
            raise ValueError("Account balance cannot be negative")

    def debit(self, amount: float, transaction_id: str) -> bool:
        """
        Debit amount from account

        Args:
            amount: Amount to debit
            transaction_id: Transaction reference

        Returns:
            True if successful, False if insufficient balance
        """
        if amount <= 0:
            raise ValueError("Debit amount must be positive")

        if not self.is_active:
            return False

        if self.balance >= amount:
            self.balance -= amount
            self.transaction_history.append(transaction_id)
            return True
        return False

    def credit(self, amount: float, transaction_id: str) -> bool:
        """
        Credit amount to account

        Args:
            amount: Amount to credit
            transaction_id: Transaction reference

        Returns:
            True if successful
        """
        if amount <= 0:
            raise ValueError("Credit amount must be positive")

        if not self.is_active:
            return False

        self.balance += amount
        self.transaction_history.append(transaction_id)
        return True

    def get_transaction_count(self) -> int:
        """Get total number of transactions"""
        return len(self.transaction_history)

    def to_dict(self) -> Dict:
        """Convert account to dictionary"""
        return {
            "account_id": self.account_id,
            "balance": self.balance,
            "creation_date": self.creation_date.isoformat(),
            "transaction_count": self.get_transaction_count(),
            "is_active": self.is_active,
            "account_type": self.account_type
        }


@dataclass
class VPA:
    """Virtual Payment Address (UPI ID) linked to an account"""

    vpa_id: str  # e.g., "user@paytm", "9876543210@ybl"
    account_id: str
    name: str
    creation_date: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    verified: bool = True
    vpa_type: str = "individual"  # individual, merchant

    def __post_init__(self):
        """Validate VPA format"""
        if "@" not in self.vpa_id:
            raise ValueError("VPA must contain '@' symbol")

    def get_handle(self) -> str:
        """Extract payment service provider handle"""
        return self.vpa_id.split("@")[1]

    def get_identifier(self) -> str:
        """Extract user identifier part"""
        return self.vpa_id.split("@")[0]

    def to_dict(self) -> Dict:
        """Convert VPA to dictionary"""
        return {
            "vpa_id": self.vpa_id,
            "account_id": self.account_id,
            "name": self.name,
            "handle": self.get_handle(),
            "creation_date": self.creation_date.isoformat(),
            "is_active": self.is_active,
            "verified": self.verified,
            "vpa_type": self.vpa_type
        }


@dataclass
class Transaction:
    """UPI transaction with complete metadata and features"""

    transaction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    from_vpa: str = ""
    to_vpa: str = ""
    amount: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    # Transaction metadata
    status: str = "pending"  # pending, success, failed, flagged, blocked
    transaction_type: str = "p2p"  # p2p, p2m (person-to-merchant)

    # Feature attributes for fraud detection
    features: Dict = field(default_factory=dict)

    # Risk assessment
    risk_score: Optional[float] = None
    risk_factors: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate transaction data"""
        if not isinstance(self.amount, (int, float)) or not math.isfinite(self.amount) or self.amount <= 0:
            raise ValueError("Transaction amount must be positive")
        if not self.from_vpa or not self.to_vpa:
            raise ValueError("Both from_vpa and to_vpa must be specified")
        if self.from_vpa == self.to_vpa:
            raise ValueError("Cannot transfer to the same VPA")
        if "@" not in self.from_vpa or "@" not in self.to_vpa:
            raise ValueError("VPAs must contain @")
        if not isinstance(self.timestamp, datetime):
            raise ValueError("timestamp must be a datetime")

    def add_feature(self, feature_name: str, feature_value) -> None:
        """Add a feature for fraud detection"""
        self.features[feature_name] = feature_value

    def update_risk_score(self, score: float, factors: List[str] = None) -> None:
        """
        Update risk assessment

        Args:
            score: Risk score (0.0 to 1.0)
            factors: List of risk factors identified
        """
        if not 0.0 <= score <= 1.0:
            raise ValueError("Risk score must be between 0.0 and 1.0")

        self.risk_score = score
        if factors:
            self.risk_factors = factors

    def mark_status(self, status: str) -> None:
        """Update transaction status"""
        valid_statuses = ["pending", "success", "failed", "flagged", "blocked"]
        if status not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        self.status = status

    def to_dict(self) -> Dict:
        """Convert transaction to dictionary"""
        return {
            "transaction_id": self.transaction_id,
            "from_vpa": self.from_vpa,
            "to_vpa": self.to_vpa,
            "amount": self.amount,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status,
            "transaction_type": self.transaction_type,
            "features": self.features,
            "risk_score": self.risk_score,
            "risk_factors": self.risk_factors
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Transaction':
        """Create transaction from dictionary"""
        transaction = cls(
            transaction_id=data.get("transaction_id", str(uuid.uuid4())),
            from_vpa=data["from_vpa"],
            to_vpa=data["to_vpa"],
            amount=data["amount"],
            timestamp=datetime.fromisoformat(data["timestamp"]) if isinstance(data.get("timestamp"), str) else data.get("timestamp", datetime.now()),
            status=data.get("status", "pending"),
            transaction_type=data.get("transaction_type", "p2p"),
            features=data.get("features", {}),
            risk_score=data.get("risk_score"),
            risk_factors=data.get("risk_factors", [])
        )
        return transaction
