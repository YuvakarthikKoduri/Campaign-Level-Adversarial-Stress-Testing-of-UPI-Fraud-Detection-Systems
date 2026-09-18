"""
Source VPA selection strategies for campaigns.

Different fraud scenarios involve different source account behaviors:
- Compromised accounts: single source VPA used repeatedly
- Coordinated fraud: small pool of compromised accounts
- Source rotation: tactical VPA diversity to avoid tracking
- Mixed reuse: primarily one source with occasional rotation

Velocity emerges naturally from VPA reuse patterns.
"""
from enum import Enum
from typing import List, Optional
import random


class VPAStrategy(Enum):
    """
    Source VPA selection strategies.

    Each strategy represents a different fraud account behavior model.
    """
    SINGLE_COMPROMISED_VPA = "single_compromised_vpa"
    SMALL_VPA_POOL = "small_vpa_pool"
    VPA_ROTATION = "vpa_rotation"
    MIXED_REUSE = "mixed_reuse"


class VPASelector:
    """
    Selects source VPAs according to configured strategy.

    Velocity emerges naturally from transaction history when same VPA
    is reused within 1-hour window.
    """

    def __init__(
        self,
        strategy: VPAStrategy,
        available_vpas: List[str],
        seed: Optional[int] = None
    ):
        """
        Initialize VPA selector.

        Args:
            strategy: VPA selection strategy
            available_vpas: Pool of available VPAs
            seed: Random seed for reproducibility
        """
        self.strategy = strategy
        self.available_vpas = available_vpas
        self.random = random.Random(seed)

        # Initialize strategy-specific state
        if strategy == VPAStrategy.SINGLE_COMPROMISED_VPA:
            # Pick one VPA to use for entire campaign
            self.primary_vpa = self.random.choice(available_vpas)

        elif strategy == VPAStrategy.SMALL_VPA_POOL:
            # Pick 2-3 VPAs to rotate among
            pool_size = min(3, len(available_vpas))
            self.vpa_pool = self.random.sample(available_vpas, pool_size)

        elif strategy == VPAStrategy.MIXED_REUSE:
            # Primary VPA used 70% of time, rotation for 30%
            self.primary_vpa = self.random.choice(available_vpas)
            self.reuse_probability = 0.7

        # VPA_ROTATION uses full pool with no state

    def select_source_vpa(self) -> str:
        """
        Select source VPA according to strategy.

        Returns:
            Selected VPA address
        """
        if self.strategy == VPAStrategy.SINGLE_COMPROMISED_VPA:
            # Always use the same compromised account
            return self.primary_vpa

        elif self.strategy == VPAStrategy.SMALL_VPA_POOL:
            # Rotate among small pool
            return self.random.choice(self.vpa_pool)

        elif self.strategy == VPAStrategy.VPA_ROTATION:
            # Random selection from full pool (original behavior)
            return self.random.choice(self.available_vpas)

        elif self.strategy == VPAStrategy.MIXED_REUSE:
            # Primarily reuse primary, occasionally rotate
            if self.random.random() < self.reuse_probability:
                return self.primary_vpa
            else:
                # Pick different VPA
                other_vpas = [v for v in self.available_vpas if v != self.primary_vpa]
                return self.random.choice(other_vpas) if other_vpas else self.primary_vpa

        else:
            raise ValueError(f"Unknown VPA strategy: {self.strategy}")

    def get_strategy_description(self) -> str:
        """Get human-readable strategy description."""
        descriptions = {
            VPAStrategy.SINGLE_COMPROMISED_VPA: "Single compromised account (all transactions from one source)",
            VPAStrategy.SMALL_VPA_POOL: "Small VPA pool (2-3 coordinated accounts)",
            VPAStrategy.VPA_ROTATION: "VPA rotation (random source selection, high diversity)",
            VPAStrategy.MIXED_REUSE: "Mixed reuse (70% primary VPA, 30% rotation)"
        }
        return descriptions.get(self.strategy, str(self.strategy))


def get_recommended_strategy(fraud_type: str, family: Optional[str] = None) -> VPAStrategy:
    """
    Get recommended VPA strategy for a fraud scenario.

    Args:
        fraud_type: "known" or "unknown"
        family: Campaign family name (optional)

    Returns:
        Recommended VPA strategy
    """
    # High-value burst fraud typically represents compromised accounts
    if family and "burst" in family.lower():
        return VPAStrategy.SINGLE_COMPROMISED_VPA

    # Slow drain might use small pool for redundancy
    if family and "drain" in family.lower():
        return VPAStrategy.SMALL_VPA_POOL

    # Beneficiary hopping with source rotation
    if family and "hopping" in family.lower():
        return VPAStrategy.MIXED_REUSE

    # Gradual escalation might test with rotation then settle
    if family and "escalation" in family.lower():
        return VPAStrategy.MIXED_REUSE

    # Default: compromised account model for known, mixed for unknown
    if fraud_type == "known":
        return VPAStrategy.SINGLE_COMPROMISED_VPA
    else:
        return VPAStrategy.MIXED_REUSE
