"""Only the approved RF/XGB interfaces; no automatic fitting or tuning."""
from pathlib import Path
import hashlib
import numpy as np

from src.data.semantic_entities import derive_seed
from src.data.semantic_provenance import feature_metadata
from src.features.schema import digest
from src.semantic_pipeline.authorization import require_permission
from src.semantic_pipeline.storage import ImmutableArtifact, sha256_file
from src.semantic_pipeline.workflow import (paths, load_split, run_metadata, verified,
                                          environment_record)
from .semantic_model import SemanticModelDetector


def parameter_record(value):
    """Represent library default NaNs explicitly rather than emitting invalid JSON."""
    if isinstance(value, np.generic):
        value = value.item()
    if type(value) is float and not np.isfinite(value):
        return {"library_nonfinite": str(value)}
    if type(value) is dict:
        return {key: parameter_record(item) for key, item in value.items()}
    if type(value) in (tuple, list):
        return [parameter_record(item) for item in value]
    if value is None or type(value) in (str, int, float, bool):
        return value
    raise ValueError("Unserializable effective model configuration")


def validate_probability_matrix(values, classes):
    values = np.asarray(values)
    class_array = np.asarray(classes)
    if (class_array.dtype.kind not in "iu" or list(classes) != [0, 1]
            or values.ndim != 2 or values.shape[1] != 2 or not len(values)
            or values.dtype.kind not in "fi" or not np.isfinite(values).all()
            or np.any(values < 0) or np.any(values > 1)
            or not np.allclose(values.sum(axis=1), 1, atol=1e-7, rtol=0)):
        raise ValueError("Invalid binary probability matrix/class ordering")
    return values[:, 1].astype(np.float64)


def _estimator(name, params):
    if name == "xgboost":
        from xgboost import XGBClassifier
        return XGBClassifier(**params)
    if name == "random_forest":
        from sklearn.ensemble import RandomForestClassifier
        return RandomForestClassifier(**params)
    raise ValueError("Only XGBoost and Random Forest are allowed")


def _deserialize(path, detector, filename):
    if detector == "xgboost" and filename == "model.json":
        model = _estimator(detector, {})
        model.load_model(path / filename)
        return model
    if detector == "random_forest" and filename == "model.joblib":
        import joblib
        return joblib.load(path / filename)  # trusted local self-produced artifacts only
    raise ValueError("Unexpected model type/serialization")


def train_model(config, *, execution_id, root, detector, permit=None):
    require_permission(permit, config, execution_id, "train")
    if detector not in config.data["models"]:
        raise ValueError("Unsupported detector")
    x, y, rows = load_split(config, execution_id=execution_id, root=root,
                           split="train", operation="train", permit=permit)
    if set(y.tolist()) != {0, 1}:
        raise ValueError("Training requires both classes; never resample silently")
    p = paths(root, execution_id)
    seed = derive_seed(config.data["root_seed"], "model", detector, bits=32)
    params = dict(config.data["models"][detector], random_state=seed)
    dataset_hash = sha256_file(p["dataset"] / "artifact_manifest.json")
    identity = digest(dict(detector=detector, params=params, dataset=dataset_hash,
                           metadata=feature_metadata(), environment=environment_record()))
    target = p["models"] / detector
    with ImmutableArtifact(target) as writer:
        estimator = _estimator(detector, params)
        from threadpoolctl import threadpool_limits
        with threadpool_limits(limits=1):
            estimator.fit(x, y)
            first = validate_probability_matrix(estimator.predict_proba(x), estimator.classes_)
        filename = "model.json" if detector == "xgboost" else "model.joblib"
        if detector == "xgboost":
            estimator.save_model(writer.stage / filename)
        else:
            import joblib
            joblib.dump(estimator, writer.stage / filename, compress=0, protocol=5)
        reloaded = _deserialize(writer.stage, detector, filename)
        with threadpool_limits(limits=1):
            second = validate_probability_matrix(reloaded.predict_proba(x), reloaded.classes_)
            third = validate_probability_matrix(reloaded.predict_proba(x), reloaded.classes_)
        if not np.array_equal(first, second) or not np.array_equal(second, third):
            raise ValueError("Reload/repeated inference is not byte-identical")
        writer.bytes("train_probabilities.f64", first.astype("<f8").tobytes())
        writer.json("training_ids.json", [r["event_id"] for r in rows])
        writer.json("configuration.json", params)
        writer.json("effective_parameters.json", parameter_record(estimator.get_params(deep=False)))
        if detector == "xgboost":
            from src.features.schema import parse_json
            writer.json("booster_configuration.json", parse_json(estimator.get_booster().save_config()))
        return writer.finish(run_metadata(
            config, execution_id, p["root"], "probability_model", permit=permit, detector=detector,
            model_id=identity, model_file=filename, model_sha256=sha256_file(writer.stage / filename),
            dataset_manifest=dataset_hash, model_seed=seed, feature_count=4,
            positive_class=1, reload_equal=True, inference_equal=True))


def load_model(path, *, permit=None, config, execution_id, operation="validate-model"):
    require_permission(permit, config, execution_id, operation)
    if operation not in ("validate-model", "validate-readiness", "calibrate"):
        raise PermissionError("Unsupported probability-model access")
    path = Path(path)
    manifest = verified(path, config, "probability_model")
    m = manifest["metadata"]
    if (m["detector"] not in {"xgboost", "random_forest"}
            or m["model_file"] != ("model.json" if m["detector"] == "xgboost" else "model.joblib")):
        raise ValueError("Unapproved model serialization path")
    if (m["execution_id"] != execution_id or m["environment"] != environment_record()
            or m["positive_class"] != 1 or m["feature_count"] != 4
            or sha256_file(path / m["model_file"]) != m["model_sha256"]):
        raise ValueError("Model provenance/environment mismatch")
    return SemanticModelDetector(_deserialize(path, m["detector"], m["model_file"]),
                                 m["feature_metadata"], m["model_id"])


def validate_model(config, *, execution_id, root, detector, permit=None):
    require_permission(permit, config, execution_id, "validate-model")
    p = paths(root, execution_id)
    x, _, rows = load_split(config, execution_id=execution_id, root=root, split="train",
                           operation="validate-model", permit=permit)
    adapter = load_model(p["models"] / detector, permit=permit, config=config, execution_id=execution_id)
    first = np.asarray([adapter.predict(v.reshape(1, 4)) for v in x], dtype="<f8").tobytes()
    expected = (p["models"] / detector / "train_probabilities.f64").read_bytes()
    if first != expected:
        raise ValueError("Persisted training inference mismatch")
    second = load_model(p["models"] / detector, permit=permit, config=config, execution_id=execution_id)
    if first != np.asarray([second.predict(v.reshape(1, 4)) for v in x], dtype="<f8").tobytes():
        raise ValueError("Independent reload mismatch")
    with ImmutableArtifact(p["evidence"] / ("model_validation_" + detector)) as writer:
        writer.json("checks.json", dict(rows=len(rows), reload_equal=True, inference_equal=True,
                                       probabilities_sha256=hashlib.sha256(first).hexdigest()))
        return writer.finish(run_metadata(config, execution_id, p["root"], "model_validation", permit=permit,
                                         model_manifest=sha256_file(
                                             p["models"] / detector / "artifact_manifest.json")))
