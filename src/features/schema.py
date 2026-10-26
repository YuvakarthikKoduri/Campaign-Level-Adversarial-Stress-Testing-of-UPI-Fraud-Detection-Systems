"""Versioned semantic contract; no model loading or data generation."""
import hashlib
import json

CONTRACT_ID = "upi_source_attempt_features/2.0.0"
FEATURE_NAMES = ("amount", "hour_of_day", "velocity_1h", "is_new_vpa")
MAX_AMOUNT_PAISE = 10**12
WINDOW_US = 3_600_000_000
SCHEMA = {
    "contract_id": CONTRACT_ID,
    "names": list(FEATURE_NAMES),
    "logical_types": ["rupees", "UTC_hour", "prior_attempt_count", "binary_source_novelty"],
    "model_dtype": "float64",
    "amount_input_unit": "integer_paise",
    "max_amount_paise": MAX_AMOUNT_PAISE,
    "window_us": WINDOW_US,
    "window": "(t-window,t],prior_sequence_only",
    "observation": "valid_scored_attempt_after_successful_processing",
    "counted_decisions": ["ALLOW", "FLAG", "BLOCK"],
    "history_regime": "isolated_namespace",
}


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False)


def parse_json(serialized):
    def pairs_without_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result

    def reject_constant(value):
        raise ValueError(f"Nonfinite JSON value: {value}")

    return json.loads(serialized, object_pairs_hook=pairs_without_duplicates,
                      parse_constant=reject_constant)


def digest(value):
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


SCHEMA_DIGEST = digest(SCHEMA)


def integer(value, name, minimum=0, maximum=2**53 - 1):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer in [{minimum}, {maximum}]")
    return value


def identifier(value, name, vpa=False):
    if (type(value) is not str or not value or value.strip() != value
            or any(ord(c) < 32 for c in value)
            or (vpa and (value.count("@") != 1 or not all(value.split("@"))
                         or any(c.isspace() for c in value)))):
        raise ValueError(f"Invalid {name}")
    return value
