#!/usr/bin/env python3
"""Academic legacy-simulator RL demonstration, separate from held Gate C workflows."""
import argparse
from pathlib import Path

from src.experiments.prototype import PrototypeConfig, compare


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Fresh output directory; never overwritten")
    parser.add_argument("--seeds", type=int, nargs="+", default=[101, 202, 303])
    parser.add_argument("--campaigns", type=int, default=12, help="Per kind, attacker, detector and seed")
    parser.add_argument("--episodes", type=int, default=300, help="RL training episodes per detector and seed")
    parser.add_argument("--max-steps", type=int, default=30)
    parser.add_argument("--detector", choices=["both", "xgboost", "random_forest"], default="both")
    parser.add_argument("--attacker", choices=["all", "static", "adaptive", "rl", "untrained_rl"], default="all")
    parser.add_argument("--flag-threshold", type=float, default=.4)
    parser.add_argument("--block-threshold", type=float, default=.7)
    parser.add_argument("--policy-dir", type=Path,
                        help="Evaluate saved policies without training; identities must match")
    args = vars(parser.parse_args(argv))
    output = args.pop("output")
    policies = args.pop("policy_dir")
    args["seeds"] = tuple(args["seeds"])
    result = compare(output, PrototypeConfig(**args), policies)
    print(f"Complete: {result['campaigns']} evaluation campaigns; "
          f"{result['training_episodes']} RL training episodes. Outputs: {output}")
    for r in result["summary"]:
        print(r["detector"], r["kind"], r["attacker"],
              f"success={r['success_mean']:.3f}", f"exposure={r['exposure_mean']:.2f}")
    return output


if __name__ == "__main__":
    main()
