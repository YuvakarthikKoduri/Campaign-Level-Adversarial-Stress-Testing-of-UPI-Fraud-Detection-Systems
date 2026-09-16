"""
Risk Threshold Configuration

Defines decision thresholds for fraud detection:
- ALLOW: Low risk, transaction proceeds normally
- FLAG: Medium risk, transaction flagged for review
- BLOCK: High risk, transaction blocked
"""

from typing import Dict, Tuple
from enum import Enum


class RiskDecision(Enum):
    """Risk-based decision outcomes"""
    ALLOW = "ALLOW"
    FLAG = "FLAG"
    BLOCK = "BLOCK"


class ThresholdConfig:
    """
    Configurable risk thresholds for transaction decisions

    Risk score ranges:
    - [0.0, flag_threshold): ALLOW - Low risk, proceed
    - [flag_threshold, block_threshold): FLAG - Medium risk, review needed
    - [block_threshold, 1.0]: BLOCK - High risk, reject transaction
    """

    def __init__(
        self,
        flag_threshold: float = 0.40,
        block_threshold: float = 0.70
    ):
        """
        Initialize threshold configuration

        Args:
            flag_threshold: Minimum score to flag transaction (default 0.40)
            block_threshold: Minimum score to block transaction (default 0.70)
        """
        self.validate_thresholds(flag_threshold, block_threshold)
        self.flag_threshold = flag_threshold
        self.block_threshold = block_threshold

    @staticmethod
    def validate_thresholds(flag: float, block: float) -> None:
        """Validate threshold values"""
        if not (0.0 <= flag <= 1.0):
            raise ValueError("Flag threshold must be between 0.0 and 1.0")
        if not (0.0 <= block <= 1.0):
            raise ValueError("Block threshold must be between 0.0 and 1.0")
        if flag >= block:
            raise ValueError("Flag threshold must be less than block threshold")

    def get_decision(self, risk_score: float) -> RiskDecision:
        """
        Determine decision based on risk score

        Args:
            risk_score: Risk score from fraud detector (0.0 to 1.0)

        Returns:
            RiskDecision: ALLOW, FLAG, or BLOCK
        """
        if not 0.0 <= risk_score <= 1.0:
            raise ValueError("Risk score must be between 0.0 and 1.0")

        if risk_score >= self.block_threshold:
            return RiskDecision.BLOCK
        elif risk_score >= self.flag_threshold:
            return RiskDecision.FLAG
        else:
            return RiskDecision.ALLOW

    def get_thresholds(self) -> Dict[str, float]:
        """Get current threshold configuration"""
        return {
            "flag": self.flag_threshold,
            "block": self.block_threshold
        }

    def update_thresholds(
        self,
        flag_threshold: float = None,
        block_threshold: float = None
    ) -> None:
        """
        Update threshold configuration

        Args:
            flag_threshold: New flag threshold (optional)
            block_threshold: New block threshold (optional)
        """
        new_flag = flag_threshold if flag_threshold is not None else self.flag_threshold
        new_block = block_threshold if block_threshold is not None else self.block_threshold

        self.validate_thresholds(new_flag, new_block)

        self.flag_threshold = new_flag
        self.block_threshold = new_block

    def get_risk_category(self, risk_score: float) -> Tuple[RiskDecision, str]:
        """
        Get decision and human-readable category

        Args:
            risk_score: Risk score from fraud detector

        Returns:
            Tuple of (decision, category_description)
        """
        decision = self.get_decision(risk_score)

        categories = {
            RiskDecision.ALLOW: "Low Risk",
            RiskDecision.FLAG: "Medium Risk - Review Required",
            RiskDecision.BLOCK: "High Risk - Transaction Blocked"
        }

        return decision, categories[decision]

    def to_dict(self) -> Dict:
        """Convert configuration to dictionary"""
        return {
            "flag_threshold": self.flag_threshold,
            "block_threshold": self.block_threshold,
            "ranges": {
                "ALLOW": f"[0.0, {self.flag_threshold})",
                "FLAG": f"[{self.flag_threshold}, {self.block_threshold})",
                "BLOCK": f"[{self.block_threshold}, 1.0]"
            }
        }


# Default threshold configuration
DEFAULT_THRESHOLDS = ThresholdConfig(
    flag_threshold=0.40,
    block_threshold=0.70
)


def get_default_thresholds() -> ThresholdConfig:
    """Get default threshold configuration"""
    return DEFAULT_THRESHOLDS


def create_conservative_thresholds() -> ThresholdConfig:
    """Create conservative threshold configuration (lower thresholds)"""
    return ThresholdConfig(
        flag_threshold=0.30,
        block_threshold=0.60
    )


def create_aggressive_thresholds() -> ThresholdConfig:
    """Create aggressive threshold configuration (higher thresholds)"""
    return ThresholdConfig(
        flag_threshold=0.50,
        block_threshold=0.80
    )
