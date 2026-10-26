"""Literal-admission primitives and explicit nonlearned collection purpose.

No batching/generation occurs here on import or environment construction.
"""
from dataclasses import asdict
import copy

import numpy as np

from src.features import extractor as shared
from src.features.events import utc_datetime
from src.data.semantic_provenance import feature_metadata, validate_feature_metadata
from src.environment.semantic import SemanticEnvironment, RunInvalid


class CollectionObserver:
    """Successful scoring stage, not a fraud-probability estimate or trained model."""
    policy_id = "nonlearned_allow_v1"

    def __init__(self):
        self.metadata = feature_metadata()

    def predict(self, vector):
        validate_feature_metadata(self.metadata)
        if (not isinstance(vector, np.ndarray) or vector.dtype != np.float64
                or vector.shape != (1, 4) or not np.isfinite(vector).all()):
            raise ValueError("Invalid shared collection vector")
        return 0.0


class GateCEnvironment(SemanticEnvironment):
    def __init__(self, namespace, predictor, *, purpose, snapshot=None, threshold_config=None):
        if purpose not in ("collection", "readiness"):
            raise ValueError("Explicit collection/readiness purpose required")
        self.purpose = purpose
        super().__init__(namespace, predictor, snapshot=snapshot, threshold_config=threshold_config)

    def _validate_predictor(self, predictor):
        from src.detectors.semantic_model import SemanticModelDetector
        expected = CollectionObserver if self.purpose == "collection" else SemanticModelDetector
        if type(predictor) is not expected:
            raise ValueError("Predictor is incompatible with declared Gate C purpose")

    def _response(self, *args):
        response = super()._response(*args)
        response["details"] = f"Gate C {self.purpose}; no recovery simulated"
        return response


def setup_collection_environment(component, entities):
    env = GateCEnvironment(component["namespace"], CollectionObserver(), purpose="collection")
    for row in sorted(entities, key=lambda r: r["vpa_id"]):
        if row["component_id"] != component["component_id"]:
            continue
        account = row["account_id"]
        if account not in env.accounts:
            env.create_account(account, row["initial_balance_paise"] / 100.0)
            env.accounts[account].creation_date = utc_datetime(row["created_time_us"])
        env.create_vpa(row["vpa_id"], account, row["vpa_id"])
        env.vpas[row["vpa_id"]].creation_date = utc_datetime(row["created_time_us"])
    return env


def admit_candidate(environment, candidate, *, journal_append=None):
    """Process one literal candidate; labels are attached only after scoring.

    This unit primitive is not a generator or batch workflow. A failed external
    journal invalidates processing and restores the prior published ledger state.
    """
    if type(environment) is not GateCEnvironment or environment.purpose != "collection":
        raise ValueError("Explicit collection environment required")
    environment._require_valid()
    original = environment._state
    try:
        prefix = environment.history.snapshot().sha256
        sequence = environment.history.next_sequence
        event = None
        try:
            if candidate.horizon_exceeded:
                raise ValueError("episode_horizon")
            event = candidate.feature_event(sequence)
        except (ValueError, TypeError) as exc:
            response = environment._invalid(str(exc), candidate.candidate_id)
        else:
            response = environment.process_event(event)
        admitted = response["execution_status"] != "invalid"
        record = {
            "kind": "admitted" if admitted else "rejected",
            "candidate": candidate.to_dict(),
            "event": asdict(event) if admitted else None,
            "features": (shared.encode_vector(shared.FeatureRecord(**response["features"])).tolist()[0]
                         if admitted else None),
            "label": {"event_id": candidate.candidate_id, "target": candidate.intent,
                      "family": candidate.family},
            "outcome": dict(response, collector_score=0.0 if admitted else None,
                            collector_policy=CollectionObserver.policy_id,
                            fraud_probability=None),
            "prefix_sha256": prefix,
            "postfix_sha256": environment.history.snapshot().sha256,
        }
        if journal_append is not None:
            journal_append(copy.deepcopy(record))
        return record
    except Exception as exc:
        environment._state = original
        environment.run_invalid = True
        raise RunInvalid("Collection/journal failure; run invalid and prior state restored") from exc
