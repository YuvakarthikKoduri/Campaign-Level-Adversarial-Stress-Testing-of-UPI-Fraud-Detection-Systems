"""Immutable experiment inputs; RNG streams never depend on global random state."""
from dataclasses import asdict, dataclass
from datetime import datetime
import hashlib
import random

METRIC_VERSION = "corrected-v2"
FEATURE_SCHEMA = ("amount", "hour_of_day", "velocity_1h", "is_new_vpa")


def derive_seed(seed, *parts):
    raw = ":".join(map(str, (seed, *parts))).encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


@dataclass(frozen=True)
class RunConfig:
    seed: int = 42
    campaigns: int = 10
    max_steps: int = 50
    max_duration_seconds: float = 86400
    simulated_start: str = "2026-01-05T12:00:00"
    flag_threshold: float = 0.40
    block_threshold: float = 0.70
    initial_balance: float = 500000
    budget: float = 500000
    max_transaction_amount: float = 50000
    feedback: str = "label_only"
    split: str = "development"
    development_seeds: tuple = ()
    accounts: tuple = tuple(f"user{i}@upi" for i in range(10))

    def __post_init__(self):
        import math
        if not isinstance(self.seed, int) or self.campaigns <= 0 or self.max_steps <= 0:
            raise ValueError("Seed, campaigns and horizon are required")
        for value in (self.max_duration_seconds, self.initial_balance, self.budget,
                      self.max_transaction_amount):
            if not math.isfinite(value) or value <= 0:
                raise ValueError("Limits must be finite and positive")
        start = datetime.fromisoformat(self.simulated_start)
        if start.tzinfo is not None:
            raise ValueError("Use naive simulated UTC timestamps consistently")
        if not 0 <= self.flag_threshold < self.block_threshold <= 1:
            raise ValueError("Invalid decision policy")
        if self.feedback not in ("label_only", "score"):
            raise ValueError("Unknown feedback channel")
        if len(set(self.accounts)) != len(self.accounts) or len(self.accounts) < 2:
            raise ValueError("Distinct source/beneficiary pool required")
        if any("@" not in a for a in self.accounts):
            raise ValueError("Invalid VPA pool")
        if self.split not in ("development", "evaluation"):
            raise ValueError("Unknown split")
        if self.split == "evaluation" and self.seed in self.development_seeds:
            raise ValueError("Evaluation seed overlaps declared development seeds")

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class CampaignSpec:
    campaign_id: str
    family: str
    fraud_type: str
    target_amount: float
    vpa_strategy: str
    start_time: str
    policy_seed: int
    timer_seed: int
    vpa_seed: int
    is_fraud: bool = True

    def to_dict(self):
        return asdict(self)


def build_workload(config):
    """Balanced family quotas, immutable shared initial conditions, separate RNGs."""
    from src.campaigns.generator import CampaignFamily
    from src.campaigns.vpa_strategy import VPAStrategy
    workload = {}
    for kind in ("known", "unknown"):
        families = (["high_value_burst"] if kind == "known" else
                    ["slow_drain", "gradual_escalation", "beneficiary_hopping"])
        rng = random.Random(derive_seed(config.seed, "workload", kind))
        specs = []
        for i in range(config.campaigns):
            family = families[i % len(families)]
            identity = f"{kind}-{i:04d}"
            specs.append(CampaignSpec(
                campaign_id=f"{config.seed}-{identity}", family=family, fraud_type=kind,
                target_amount=round(rng.uniform(20000, 40000) if kind == "known"
                                    else rng.uniform(10000, 20000), 2),
                vpa_strategy=(VPAStrategy.SINGLE_COMPROMISED_VPA.value if kind == "known"
                              else VPAStrategy.MIXED_REUSE.value),
                start_time=config.simulated_start,
                policy_seed=derive_seed(config.seed, identity, "policy"),
                timer_seed=derive_seed(config.seed, identity, "timer"),
                vpa_seed=derive_seed(config.seed, identity, "vpa")))
        workload[kind] = tuple(specs)
    return workload
