"""
UPI Fraud Stress Lab - Environment Module

Provides UPI transaction environment simulation with:
- Account and VPA management
- Transaction processing with fraud detection
- Risk-based decision making (ALLOW/FLAG/BLOCK)
"""

from .entities import Account, VPA, Transaction
from .simulator import UPIEnvironment
from .thresholds import (
    ThresholdConfig,
    RiskDecision,
    get_default_thresholds,
    create_conservative_thresholds,
    create_aggressive_thresholds
)

__all__ = [
    # Entities
    "Account",
    "VPA",
    "Transaction",

    # Simulator
    "UPIEnvironment",

    # Thresholds
    "ThresholdConfig",
    "RiskDecision",
    "get_default_thresholds",
    "create_conservative_thresholds",
    "create_aggressive_thresholds",
]
