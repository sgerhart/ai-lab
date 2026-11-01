#!/usr/bin/env python3
"""CLI utility to execute the Apple Silicon Reinforcement Learning (GRPO) compatibility spike."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
for p in (PROJECT_ROOT, PROJECT_ROOT / "packages", PROJECT_ROOT / "services"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from packages.contracts import RLConfig
from services.model.rl_spike import RLCompatibilitySpike


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Apple Silicon RL (GRPO) compatibility spike and gradient verification."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="reports/rl_spike_report.json",
        help="Destination path for RL spike findings report JSON (default: reports/rl_spike_report.json)",
    )
    parser.add_argument(
        "--group-size",
        type=int,
        default=4,
        help="Number of rollouts per prompt group (default: 4)",
    )
    parser.add_argument(
        "--beta",
        type=float,
        default=0.04,
        help="KL divergence penalty coefficient (default: 0.04)",
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=1e-4,
        help="Policy optimizer learning rate (default: 1e-4)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print("=" * 70)
    print("AI Lab — Execution-Verified RL Compatibility Spike (WO-07)")
    print("=" * 70)
    print(f"Group Size (G)    : {args.group_size}")
    print(f"KL Penalty Beta   : {args.beta}")
    print(f"Learning Rate     : {args.learning_rate}")
    print("-" * 70)

    config = RLConfig(
        group_size=args.group_size,
        beta=args.beta,
        learning_rate=args.learning_rate,
    )
    spike = RLCompatibilitySpike(config=config)
    report = spike.run_spike()

    out_path = Path(args.output)
    if not out_path.is_absolute():
        out_path = PROJECT_ROOT / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(), f, indent=2)

    print(f"Spike ID          : {report.spike_id}")
    print(f"Framework Target  : {report.framework}")
    print(f"Device Target     : {report.device_arch}")
    print(f"Step Verified     : {report.gradient_step_verified}")
    print(f"Loss Finite       : {report.loss_finite} (total_loss={report.step_result.total_loss:.6f})")
    print(f"Policy Loss       : {report.step_result.policy_loss:.6f}")
    print(f"KL Penalty        : {report.step_result.kl_penalty:.6f}")
    print(f"Mean Advantage    : {report.step_result.mean_advantage:.6f}")
    print(f"Gradient Norm     : {report.step_result.gradient_norm:.6f}")
    print(f"Weights Diverged  : {report.step_result.weights_diverged}")
    print(f"Initial Hash      : {report.step_result.initial_param_hash[:16]}...")
    print(f"Updated Hash      : {report.step_result.updated_param_hash[:16]}...")
    print("-" * 70)
    print("Key Findings:")
    for finding in report.findings:
        print(f"  • {finding}")
    print("-" * 70)
    print(f"Recommendation    : {report.recommendation}")
    print(f"Report Written To : {out_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
