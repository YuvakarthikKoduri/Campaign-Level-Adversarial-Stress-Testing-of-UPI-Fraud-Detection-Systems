"""Frozen, versioned engineering assumptions, not empirical UPI parameters."""
import math
from dataclasses import dataclass
from pathlib import Path

from src.data.semantic_provenance import validate_feature_metadata
from src.features import timestamp_us
from src.features.schema import canonical_json, digest, integer, parse_json, WINDOW_US

DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "configs/semantic_v2/gate_c_v1.json"
SPLITS = ("train", "validation", "test")
FAMILIES = ("high_value_burst", "slow_drain", "gradual_escalation", "beneficiary_hopping")


def number(value, name, low=0, high=1e12, *, open_low=False):
    if (type(value) not in (int, float) or not math.isfinite(value)
            or value < low or value > high or (open_low and value == low)):
        raise ValueError(f"Invalid numeric configuration: {name}")
    return value


def validate_config(d):
    required = {"format", "base_commit", "synthetic_engineering_assumptions", "feature_metadata",
                "root_seed", "seed_derivation", "profiles", "entities", "behavior", "splits",
                "models", "policy"}
    if set(d) != required or d["format"] != "upi_gate_c_config/1":
        raise ValueError("Unknown/incomplete configuration format")
    if d["base_commit"] != "6b543895769d4e355d775b05c3a3f01f3c1ca8ef":
        raise ValueError("Unreviewed implementation base")
    if d["synthetic_engineering_assumptions"] is not True:
        raise ValueError("Synthetic assumptions must be explicit")
    validate_feature_metadata(d["feature_metadata"])
    integer(d["root_seed"], "root_seed")
    if d["seed_derivation"] != "upi-gc-seed-v1":
        raise ValueError("Unsupported seed derivation")
    if set(d["profiles"]) != {"pilot", "baseline"}:
        raise ValueError("Both bounded profiles required")
    for profile in d["profiles"].values():
        if set(profile) != {"components", "candidate_cap", "split_counts", "attack_start", "attack_length"}:
            raise ValueError("Unknown profile setting")
        for key in ("components", "candidate_cap", "attack_length"):
            integer(profile[key], key, 1, 1_000_000)
        if len(profile["split_counts"]) != 3:
            raise ValueError("Three explicit component counts required")
        for count in profile["split_counts"]:
            integer(count, "split component count", 1)
        if sum(profile["split_counts"]) != profile["components"]:
            raise ValueError("Component membership count mismatch")
        start = profile["attack_start"]
        if len(start) != 2 or not 0 <= start[0] <= start[1]:
            raise ValueError("Invalid intent interval")
        for value in start:
            integer(value, "intent start")
        if start[1] + profile["attack_length"] > profile["candidate_cap"]:
            raise ValueError("Intent interval exceeds proposal budget")
    e = d["entities"]
    if set(e) != {"accounts", "vpas_per_account", "initial_balance"}:
        raise ValueError("Unknown entity configuration")
    for key in ("accounts", "vpas_per_account"):
        pair = e[key]
        if len(pair) != 2 or pair[0] > pair[1]:
            raise ValueError("Invalid entity range")
        for value in pair:
            integer(value, key, 1, 1000)
    if e["accounts"][0] < 2:
        raise ValueError("Distinct source/beneficiary accounts required")
    if set(d["splits"]) != set(SPLITS):
        raise ValueError("Explicit temporal windows required")
    last_end = None
    for name in SPLITS:
        window = d["splits"][name]
        if len(window) != 2:
            raise ValueError("Malformed time window")
        start, end = map(timestamp_us, window)
        if end - start <= d["behavior"]["episode_seconds"] * 1_000_000:
            raise ValueError("Window too short")
        if last_end is not None and start - last_end < WINDOW_US:
            raise ValueError("Temporal embargo violation")
        last_end = end
    b = d["behavior"]
    behavior_keys = {
        "episode_seconds", "mixed_component_probability", "merchant_probability",
        "same_time_probability", "benign_high_value_probability", "benign_short_delay_probability",
        "benign_source_reuse", "fraud_source_reuse", "benign_payee_reuse",
        "amount_minimum_rupees", "amount_maximum_rupees", "individual_amount", "merchant_amount",
        "burst_amount", "drain_amount", "routine_delay", "drain_delay", "short_delay_mean",
        "hopping_delay", "escalation_delay", "delay_clip_seconds", "escalation_start",
        "escalation_multiplier", "escalation_jitter_sigma", "families", "family_probabilities"}
    if set(b) != behavior_keys:
        raise ValueError("Missing/unknown behavioral configuration")
    integer(b["episode_seconds"], "episode duration", 1, 86400)
    for key in ("individual_amount", "merchant_amount", "drain_amount", "routine_delay", "drain_delay"):
        if set(b[key]) != {"median", "sigma"}:
            raise ValueError("Incomplete distribution recipe")
    if (set(b["burst_amount"]) != {"median", "sigma", "minimum"}
            or set(e["initial_balance"]) != {"median", "sigma", "minimum", "maximum"}):
        raise ValueError("Incomplete balance/burst recipe")
    if tuple(b["families"]) != FAMILIES:
        raise ValueError("Unreviewed process-family set")
    weights = b["family_probabilities"]
    if type(weights) is not list or len(weights) != len(FAMILIES):
        raise ValueError("Explicit family mixture probabilities required")
    for value in weights:
        number(value, "family probability", 0, 1)
    if not math.isclose(sum(weights), 1, abs_tol=1e-12, rel_tol=0):
        raise ValueError("Family probabilities must sum to one")
    for key, value in b.items():
        if key in ("families", "family_probabilities"):
            continue
        if key.endswith("probability") or key.endswith("reuse"):
            number(value, key, 0, 1)
        elif type(value) in (int, float):
            number(value, key, 0, open_low=True)
        elif type(value) is list:
            if len(value) != 2 or value[0] > value[1]:
                raise ValueError("Invalid behavioral range")
            for item in value:
                number(item, key, 0, open_low=True)
        elif type(value) is dict:
            for item, scalar in value.items():
                number(scalar, key + "." + item, 0, open_low=True)
        else:
            raise ValueError("Unsupported behavioral parameter")
    for value in e["initial_balance"].values():
        number(value, "initial balance", 0, open_low=True)
    if not e["initial_balance"]["minimum"] <= e["initial_balance"]["median"] <= e["initial_balance"]["maximum"]:
        raise ValueError("Invalid initial-balance range")
    if e["initial_balance"]["maximum"] > 10**10:
        raise ValueError("Initial balance exceeds the approved integer ledger bound")
    if not b["amount_minimum_rupees"] <= b["amount_maximum_rupees"] <= 50000:
        raise ValueError("Unreviewed action amount limit")
    if set(d["models"]) != {"xgboost", "random_forest"}:
        raise ValueError("Only the two approved model types are allowed")
    for params in d["models"].values():
        integer(params["n_estimators"], "n_estimators", 1, 10000)
        if type(params["n_jobs"]) is not int or params["n_jobs"] != 1:
            raise ValueError("Deterministic single-worker fitting required")
    xgb = d["models"]["xgboost"]
    xgb_keys = {"n_estimators", "max_depth", "learning_rate", "min_child_weight", "subsample",
                "colsample_bytree", "reg_lambda", "scale_pos_weight", "objective", "eval_metric",
                "tree_method", "device", "n_jobs"}
    rf_keys = {"n_estimators", "max_depth", "min_samples_leaf", "max_features", "bootstrap",
               "class_weight", "n_jobs"}
    if set(xgb) != xgb_keys or set(d["models"]["random_forest"]) != rf_keys:
        raise ValueError("Unknown/missing model parameter; hidden tuning inputs forbidden")
    if (xgb["device"] != "cpu" or xgb["tree_method"] != "hist"
            or xgb["objective"] != "binary:logistic"):
        raise ValueError("Unreviewed XGBoost execution mode")
    integer(xgb["max_depth"], "XGBoost depth", 1, 32)
    for key in ("learning_rate", "subsample", "colsample_bytree"):
        number(xgb[key], key, 0, 1, open_low=True)
    for key in ("min_child_weight", "reg_lambda"):
        number(xgb[key], key, 0)
    number(xgb["scale_pos_weight"], "class weight", 0, open_low=True)
    if xgb["eval_metric"] != "logloss":
        raise ValueError("Unreviewed training diagnostic")
    rf = d["models"]["random_forest"]
    if rf["max_depth"] is not None:
        integer(rf["max_depth"], "RF depth", 1, 64)
    integer(rf["min_samples_leaf"], "RF minimum leaf", 1)
    if (type(rf["bootstrap"]) is not bool or rf["class_weight"] not in (None, "balanced", "balanced_subsample")
            or rf["max_features"] not in (None, "sqrt", "log2")):
        raise ValueError("Unreviewed RF parameter domain")
    p = d["policy"]
    if set(p) != {"objective", "grid_step", "benign_block_budget", "benign_review_budget",
                  "minimum_benign_rows", "minimum_fraud_rows", "minimum_benign_components",
                  "minimum_fraud_components"}:
        raise ValueError("Incomplete/unknown calibration configuration")
    if p["objective"] != "recall_under_benign_budgets_v1":
        raise ValueError("Unknown calibration objective")
    for key in ("benign_block_budget", "benign_review_budget"):
        number(p[key], key, 0, 1)
    if p["benign_block_budget"] > p["benign_review_budget"]:
        raise ValueError("Blocking budget exceeds review budget")
    number(p["grid_step"], "grid_step", .0001, 1)
    if abs(round(1 / p["grid_step"]) * p["grid_step"] - 1) > 1e-12:
        raise ValueError("Grid must partition [0,1]")
    for key in p:
        if key.startswith("minimum_"):
            integer(p[key], key, 1)


@dataclass(frozen=True)
class PipelineConfig:
    payload_json: str

    def __post_init__(self):
        value = parse_json(self.payload_json)
        if self.payload_json != canonical_json(value):
            raise ValueError("Configuration must be canonical and immutable")
        validate_config(value)

    @classmethod
    def from_dict(cls, data):
        if type(data) is not dict:
            raise ValueError("Configuration must be an object")
        # Round-trip detaches callers' mutable dictionaries.
        frozen = canonical_json(data)
        validate_config(parse_json(frozen))
        return cls(frozen)

    @property
    def data(self):
        return parse_json(self.payload_json)

    @property
    def digest(self):
        return digest(self.data)

    @property
    def generation_digest(self):
        return digest({k: v for k, v in self.data.items() if k not in ("models", "policy")})


def load_config(path=DEFAULT_CONFIG):
    return PipelineConfig.from_dict(parse_json(Path(path).read_text(encoding="utf-8")))
