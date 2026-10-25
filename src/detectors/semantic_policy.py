"""Three-way decision policy separate from the probability model."""
from fractions import Fraction
import math
import numpy as np

from src.features.schema import digest
from src.semantic_pipeline.authorization import require_permission
from src.semantic_pipeline.storage import ImmutableArtifact, sha256_file
from src.semantic_pipeline.workflow import paths, load_split, run_metadata


def thresholds(flag, block):
    if (type(flag) not in (int, float) or type(block) not in (int, float)
            or not math.isfinite(flag) or not math.isfinite(block)
            or not 0 <= flag < block <= 1):
        raise ValueError("Require 0 <= FLAG < BLOCK <= 1")


def policy_counts(scores, labels, flag, block):
    thresholds(flag, block)
    if len(scores) != len(labels) or not scores:
        raise ValueError("Nonempty aligned scores and labels required")
    result = dict(benign=0, fraud=0, block_fp=0, review_fp=0, block_tp=0, review_tp=0)
    for score, label in zip(scores, labels):
        if (type(label) is not int or label not in (0, 1)
                or type(score) not in (int, float) or not math.isfinite(score)
                or not 0 <= score <= 1):
            raise ValueError("Invalid score or label")
        result["fraud" if label else "benign"] += 1
        result["block_tp" if label else "block_fp"] += int(score >= block)
        result["review_tp" if label else "review_fp"] += int(score >= flag)
    return result


def feasible_counts(counts, block_budget, review_budget):
    if counts["benign"] <= 0 or counts["fraud"] <= 0:
        return False
    return (Fraction(counts["block_fp"], counts["benign"]) <= Fraction(str(block_budget))
            and Fraction(counts["review_fp"], counts["benign"]) <= Fraction(str(review_budget)))


def ranking_key(counts, flag, block):
    # Fixed support denominators: maximizing TP counts maximizes validation recall.
    return (counts["block_tp"], counts["review_tp"], -counts["block_fp"],
            -counts["review_fp"], block, flag)


def calibrate(config, *, execution_id, root, detector, permit=None):
    require_permission(permit, config, execution_id, "calibrate")
    from .semantic_train import load_model
    p = paths(root, execution_id)
    x, y, rows = load_split(config, execution_id=execution_id, root=root, split="validation",
                           operation="calibrate", permit=permit)
    policy = config.data["policy"]
    supports = {}
    for label, name in ((0, "benign"), (1, "fraud")):
        mask = y == label
        groups = {row["namespace"] for row, target in zip(rows, y.tolist()) if target == label}
        supports[name] = int(mask.sum())
        supports[name + "_components"] = len(groups)
        if (supports[name] < policy["minimum_" + name + "_rows"]
                or len(groups) < policy["minimum_" + name + "_components"]):
            raise ValueError("Insufficient validation support; no automatic policy relaxation")
    adapter = load_model(p["models"] / detector, config=config, execution_id=execution_id,
                         permit=permit, operation="calibrate")
    scores = np.asarray([adapter.predict(v.reshape(1, 4)) for v in x])
    steps = round(1 / policy["grid_step"])
    grid = [float(Fraction(i, steps)) for i in range(steps + 1)]
    benign, fraud = np.sort(scores[y == 0]), np.sort(scores[y == 1])
    fp = len(benign) - np.searchsorted(benign, grid, side="left")
    tp = len(fraud) - np.searchsorted(fraud, grid, side="left")
    best = None
    for fi, flag in enumerate(grid[:-1]):
        for bi in range(fi + 1, len(grid)):
            block = grid[bi]
            counts = dict(benign=len(benign), fraud=len(fraud), block_fp=int(fp[bi]),
                          review_fp=int(fp[fi]), block_tp=int(tp[bi]), review_tp=int(tp[fi]))
            if feasible_counts(counts, policy["benign_block_budget"], policy["benign_review_budget"]):
                key = ranking_key(counts, flag, block)
                if best is None or key > best[0]:
                    best = key, flag, block, counts
    if best is None:
        raise ValueError("No feasible policy on the predefined grid")
    _, flag, block, counts = best
    record = dict(format="upi_decision_policy/1", flag_threshold=flag, block_threshold=block,
                  comparison="score>=threshold", model_id=adapter.model_id,
                  objective=policy["objective"], budgets=policy, counts=counts, supports=supports,
                  validation_ids_sha256=digest([r["event_id"] for r in rows]),
                  dataset_manifest=sha256_file(p["dataset"] / "artifact_manifest.json"),
                  model_manifest=sha256_file(p["models"] / detector / "artifact_manifest.json"))
    record["policy_id"] = digest(record)
    with ImmutableArtifact(p["models"] / "policies" / detector) as writer:
        writer.json("policy.json", record)
        return writer.finish(run_metadata(config, execution_id, p["root"], "decision_policy", permit=permit,
                                         policy_id=record["policy_id"], model_id=adapter.model_id))
