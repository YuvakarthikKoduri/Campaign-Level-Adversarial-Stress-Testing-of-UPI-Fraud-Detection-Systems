"""Model guards and pure probability validation; no fit, reload, or model scoring."""
import numpy as np
import pytest

from src.detectors.semantic_train import train_model, load_model, validate_probability_matrix
from src.semantic_pipeline.authorization import ExecutionDenied
from src.semantic_pipeline.config import load_config, DEFAULT_CONFIG
from src.semantic_pipeline.integrity import authorize_split


@pytest.mark.parametrize("name", ["xgboost", "random_forest"])
def test_fit_interface_blocked_before_estimators_or_data(name, tmp_path):
    with pytest.raises(ExecutionDenied):
        train_model(load_config(DEFAULT_CONFIG), execution_id="no", root=tmp_path,
                    detector=name, permit=None)
    assert list(tmp_path.iterdir()) == []


def test_reload_interface_blocked_without_execution_approval(tmp_path):
    with pytest.raises(ExecutionDenied):
        load_model(tmp_path / "absent", permit=None, config=load_config(DEFAULT_CONFIG),
                   execution_id="no")


def test_positive_probability_mapping_and_invalid_outputs():
    result = validate_probability_matrix(np.array([[.8, .2], [.1, .9]]), [0, 1])
    assert result.tolist() == [.2, .9]
    for values, classes in [
        (np.array([[.5, .5]]), [1, 0]),
        (np.array([[float("nan"), .5]]), [0, 1]),
        (np.array([[.5, 1.2]]), [0, 1]),
        (np.array([[.5, .4]]), [0, 1]),
    ]:
        with pytest.raises(ValueError):
            validate_probability_matrix(values, classes)


@pytest.mark.parametrize("operation", ["train", "calibrate", "validate-model"])
def test_final_test_model_access_is_never_permitted(operation):
    with pytest.raises(PermissionError):
        authorize_split(operation, "test")
    authorize_split("train", "train")
    authorize_split("calibrate", "validation")
    authorize_split("validate-model", "train")
