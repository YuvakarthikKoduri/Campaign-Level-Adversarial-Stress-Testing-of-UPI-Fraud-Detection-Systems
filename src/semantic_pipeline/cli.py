"""No default execution approval. All commands stop before workflow access without it."""
import argparse
import sys
from .authorization import ExecutionDenied, ExecutionPermit, PHASES, require_permission
from .config import DEFAULT_CONFIG, load_config


def main(argv=None):
    parser = argparse.ArgumentParser(description="Gate C: separately approved local execution only")
    parser.add_argument("command", choices=sorted(PHASES))
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--execution-id", required=True)
    parser.add_argument("--root", default=".")
    parser.add_argument("--approval-file")
    parser.add_argument("--profile", choices=("pilot", "baseline"), default="baseline")
    parser.add_argument("--detector", choices=("xgboost", "random_forest"))
    parser.add_argument("--other-execution-id")
    args = parser.parse_args(argv)
    try:
        if not args.approval_file:
            raise ExecutionDenied("Separate execution approval file required; implementation approval is insufficient")
        config = load_config(args.config)
        permit = ExecutionPermit.load(args.approval_file)
        require_permission(permit, config, args.execution_id, args.command)
        from . import workflow, review
        from src.detectors import semantic_train, semantic_policy
        commands = {
            "preflight": workflow.preflight, "collect": workflow.collect, "prepare": workflow.prepare,
            "validate-dataset": workflow.validate_dataset, "train": semantic_train.train_model,
            "calibrate": semantic_policy.calibrate, "validate-model": semantic_train.validate_model,
            "validate-readiness": review.validate_readiness, "verify-preservation": review.verify_preservation,
            "compare-repeats": review.compare_repeats, "close-review": review.close_review}
        kwargs = dict(execution_id=args.execution_id, root=args.root, permit=permit)
        if args.command in ("preflight", "collect"):
            kwargs["profile"] = args.profile
        if args.command in ("train", "calibrate", "validate-model", "validate-readiness"):
            if args.detector is None:
                raise ValueError("Explicit --detector is required")
            kwargs["detector"] = args.detector
        if args.command in ("compare-repeats", "close-review"):
            if args.other_execution_id is None:
                raise ValueError("Explicit --other-execution-id is required")
            kwargs["other_execution_id"] = args.other_execution_id
        # A per-command immutable receipt substitutes for a mutable run journal.
        # This occurs only after a separately authorized execution entry.
        from .storage import ImmutableArtifact
        suffix = args.detector or args.other_execution_id or args.profile
        from .authorization import safe_name
        receipt = workflow.paths(args.root, args.execution_id)["evidence"] / "invocations" / (
            args.command + "_" + safe_name(suffix))
        with ImmutableArtifact(receipt) as writer:
            writer.json("request.json", dict(command=args.command, config_digest=config.digest,
                        execution_id=args.execution_id, detector=args.detector,
                        profile=args.profile, other_execution_id=args.other_execution_id,
                        approval_reference=permit.approval_reference))
            result = commands[args.command](config, **kwargs)
            writer.json("outcome.json", dict(status="completed", artifact_path=str(result)))
            writer.finish({"kind": "command_receipt", "config_digest": config.digest})
        print(result)
        return 0
    except (ValueError, PermissionError, OSError) as exc:
        print(f"Gate C denied/failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
