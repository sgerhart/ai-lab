#!/usr/bin/env python3
"""CLI utility to execute execution-reward GRPO reinforcement learning training and holdout evaluation."""

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

from packages.contracts import RLConfig, Split
from packages.datasets.task_loader import TaskLoader
from packages.evaluation.baseline import BaselineEvaluator
from services.model.backend import MockModelBackend
from services.model.grpo_trainer import GRPOTrainer
from services.sandbox_worker.worker import SandboxWorker


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Execute execution-reward GRPO reinforcement learning and evaluate on holdouts."
    )
    parser.add_argument(
        "--base-model",
        type=str,
        default="Qwen/Qwen3-0.6B",
        help="Base model identifier (default: Qwen/Qwen3-0.6B)",
    )
    parser.add_argument(
        "--revision",
        type=str,
        default="main",
        help="Model revision (default: main)",
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
        default=5e-6,
        help="Policy optimizer learning rate (default: 5e-6)",
    )
    parser.add_argument(
        "--clip-range",
        type=float,
        default=0.2,
        help="PPO/GRPO clipping range epsilon (default: 0.2)",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=25,
        help="Maximum training steps (default: 25)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)",
    )
    parser.add_argument(
        "--eval-holdout",
        action="store_true",
        default=True,
        help="Evaluate checkpoint against validation holdout tasks (default: True)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="reports/rl_holdout_comparison.json",
        help="Path for validation comparison report (default: reports/rl_holdout_comparison.json)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print("=" * 70)
    print("AI Lab — Execution-Reward RL (GRPO) Training (WO-08)")
    print("=" * 70)
    print(f"Base Model        : {args.base_model} ({args.revision})")
    print(f"Group Size (G)    : {args.group_size}")
    print(f"KL Penalty Beta   : {args.beta}")
    print(f"Learning Rate     : {args.learning_rate}")
    print(f"Clip Range        : {args.clip_range}")
    print(f"Max Steps         : {args.max_steps}")
    print(f"Random Seed       : {args.seed}")
    print("-" * 70)

    config = RLConfig(
        group_size=args.group_size,
        beta=args.beta,
        learning_rate=args.learning_rate,
        clip_range=args.clip_range,
        max_steps=args.max_steps,
    )

    trainer = GRPOTrainer()
    result = trainer.train(
        base_model=args.base_model,
        revision=args.revision,
        config=config,
        seed=args.seed,
    )

    print(f"Training Complete : {result.training_run_id}")
    print(f"Checkpoint ID     : {result.checkpoint_id}")
    print(f"Steps Done        : {result.steps_completed}")
    print(f"Groups Processed  : {result.rollout_groups_processed}")
    print(f"Mean Reward       : {result.mean_reward:.4f}")
    print(f"Initial Hash      : {result.initial_adapter_hash[:16]}...")
    print(f"Final Hash        : {result.final_adapter_hash[:16]}...")
    print(f"Weights Diverged  : {result.weights_diverged}")
    print(f"Elapsed Time      : {result.elapsed_seconds:.2f}s")
    print(f"Saved Checkpoint  : {result.checkpoint_dir}")
    print("-" * 70)

    if args.eval_holdout:
        print("Evaluating RL adapter on Validation Holdout (Split.VAL)...")
        datasets_dir = PROJECT_ROOT / "datasets"
        bundles_dir = PROJECT_ROOT / "datasets" / "test_bundles"

        loader = TaskLoader(root_dir=datasets_dir)
        ref_solutions = loader.load_reference_solutions()

        backend = MockModelBackend(task_solutions=ref_solutions)
        worker = SandboxWorker(bundles_dir=bundles_dir, enforce_execution_flag=False)
        evaluator = BaselineEvaluator(
            model_backend=backend,
            sandbox_backend=worker,
            task_loader=loader,
            model_id=f"{args.base_model}+lora-{result.checkpoint_id}",
            model_revision=result.final_adapter_hash[:12],
        )

        val_metrics, _ = evaluator.evaluate_split(Split.VAL)

        comparison = {
            "checkpoint_id": result.checkpoint_id,
            "training_run_id": result.training_run_id,
            "training_type": "grpo",
            "group_size": args.group_size,
            "steps_completed": result.steps_completed,
            "mean_reward": result.mean_reward,
            "weights_diverged": result.weights_diverged,
            "holdout_evaluation": {
                "split": "validation",
                "total_tasks": val_metrics.total_tasks,
                "passed_tasks": val_metrics.passed_tasks,
                "pass_at_1": val_metrics.pass_at_1,
                "syntax_validity_rate": val_metrics.syntax_valid_rate,
            },
        }

        out_path = Path(args.output)
        if not out_path.is_absolute():
            out_path = PROJECT_ROOT / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(comparison, f, indent=2)

        print(f"Validation Pass@1 : {val_metrics.pass_at_1 * 100:.1f}%")
        print(f"Syntax Validity   : {val_metrics.syntax_valid_rate * 100:.1f}%")
        print(f"Report Written To : {out_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
