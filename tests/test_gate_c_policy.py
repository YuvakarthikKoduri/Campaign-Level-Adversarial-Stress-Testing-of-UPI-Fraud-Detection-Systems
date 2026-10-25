"""Literal count math only; the calibration/search procedure is never run."""
import pytest

from src.detectors.semantic_policy import policy_counts, feasible_counts, ranking_key, calibrate
from src.semantic_pipeline.config import load_config, DEFAULT_CONFIG
from src.semantic_pipeline.authorization import ExecutionDenied


def test_literal_three_way_counts_and_exact_budget_boundary():
    counts = policy_counts([.1, .4, .7, .9], [0, 0, 1, 1], .4, .7)
    assert counts == dict(benign=2, fraud=2, block_fp=0, review_fp=1, block_tp=2, review_tp=2)
    assert feasible_counts(dict(benign=100, fraud=1, block_fp=1, review_fp=5,
                                block_tp=1, review_tp=1), .01, .05)
    assert not feasible_counts(dict(benign=100, fraud=1, block_fp=2, review_fp=5,
                                    block_tp=1, review_tp=1), .01, .05)
    assert ranking_key(counts, .4, .7) > ranking_key(dict(counts, block_tp=1), .4, .7)


@pytest.mark.parametrize("f,b", [(.7, .4), (.5, .5), (-.1, .7), (.4, 1.1)])
def test_invalid_policy_thresholds(f, b):
    with pytest.raises(ValueError):
        policy_counts([.2], [0], f, b)


def test_calibration_procedure_not_executed_without_permission(tmp_path):
    with pytest.raises(ExecutionDenied):
        calibrate(load_config(DEFAULT_CONFIG), execution_id="no", root=tmp_path,
                  detector="xgboost", permit=None)
    assert list(tmp_path.iterdir()) == []
