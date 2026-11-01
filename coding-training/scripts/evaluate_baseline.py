#!/usr/bin/env python3
"""CLI utility to run reproducible baseline holdout evaluations."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

# Ensure coding-training packages and services are in PYTHONPATH
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
for p in (PROJECT_ROOT, PROJECT_ROOT / "packages", PROJECT_ROOT / "services"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from packages.contracts import GenerationConfig, SandboxPolicy, Split
from packages.datasets.task_loader import TaskLoader
from packages.evaluation.baseline import BaselineEvaluator
from services.model.backend import MLXModelBackend, MockModelBackend, ModelBackend
from services.sandbox_worker.worker import SandboxWorker


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run reproducible holdout baseline evaluation on curated coding tasks."
    )
    parser.add_argument(
        "--splits",
        type=str,
        default="val,test",
        help="Comma-separated splits to evaluate: train,val,test (default: val,test)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="reports/baseline_holdout.json",
        help="Output JSON report file path (default: reports/baseline_holdout.json)",
    )
    parser.add_argument(
        "--model-id",
        type=str,
        default="Qwen/Qwen3-0.6B",
        help="Model identifier (default: Qwen/Qwen3-0.6B)",
    )
    parser.add_argument(
        "--revision",
        type=str,
        default="main",
        help="Model git commit revision or tag (default: main)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="PRNG seed for reproducible generation (default: 42)",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.2,
        help="Sampling temperature (default: 0.2)",
    )
    parser.add_argument(
        "--use-reference",
        action="store_true",
        help="Evaluate reference solutions to verify ground-truth ceiling (100% pass@1).",
    )
    parser.add_argument(
        "--backend",
        type=str,
        choices=["mlx", "mock"],
        default="mock",
        help="Model backend engine: 'mlx' for local Apple Silicon, 'mock' for dry-run/CI (default: mock)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    task_loader = TaskLoader(PROJECT_ROOT / "datasets")

    # Determine splits
    split_names = [s.strip().lower() for s in args.splits.split(",") if s.strip()]
    target_splits: list[Split] = []
    for name in split_names:
        try:
            target_splits.append(Split(name))
        except ValueError:
            print(f"Error: Unknown split '{name}'. Valid splits: train, val, test", file=sys.stderr)
            return 1

    print("============================================================")
    print("AI Lab Coding Training — Baseline Holdout Evaluation")
    print(f"Model ID:    {args.model_id} ({args.revision})")
    print(f"Backend:     {args.backend}")
    print(f"Reference:   {args.use_reference}")
    print(f"Splits:      {', '.join(s.value for s in target_splits)}")
    print(f"Seed:        {args.seed}")
    print("============================================================")

    # Configure ModelBackend
    model_backend: ModelBackend
    if args.use_reference:
        ref_solutions = task_loader.load_reference_solutions()
        model_backend = MockModelBackend(task_solutions=ref_solutions)
        model_backend.load(args.model_id, args.revision)
    elif args.backend == "mlx":
        model_backend = MLXModelBackend(dry_run_fallback=True)
        model_backend.load(args.model_id, args.revision)
    else:
        model_backend = MockModelBackend()
        model_backend.load(args.model_id, args.revision)

    # Configure SandboxBackend
    # Local worker with execution enabled for evaluation run
    sandbox_worker = SandboxWorker(
        bundles_dir=PROJECT_ROOT / "datasets" / "test_bundles",
        enforce_execution_flag=False,
    )

    policy = SandboxPolicy(
        wall_timeout_seconds=5.0,
        memory_limit_mb=512,
        stdout_limit_bytes=65536,
        stderr_limit_bytes=65536,
    )

    gen_config = GenerationConfig(
        temperature=args.temperature,
        seed=args.seed,
    )

    evaluator = BaselineEvaluator(
        model_backend=model_backend,
        sandbox_backend=sandbox_worker,
        task_loader=task_loader,
        policy=policy,
        model_id=args.model_id,
        model_revision=args.revision,
    )

    print(f"Starting evaluation across {len(target_splits)} splits...")
    report = evaluator.evaluate_holdout(
        splits=target_splits,
        generation_config=gen_config,
        seed=args.seed,
        metadata={
            "use_reference": args.use_reference,
            "backend": args.backend,
        },
    )

    # Print Summary Table
    print("\n" + "=" * 60)
    print(f"{'Split':<10} | {'Total':<6} | {'Passed':<6} | {'Pass@1':<8} | {'Mean Rew':<8} | {'Valid %':<8}")
    print("-" * 60)
    for split_val, metrics in report.splits.items():
        print(
            f"{split_val:<10} | "
            f"{metrics.total_tasks:<6} | "
            f"{metrics.passed_tasks:<6} | "
            f"{metrics.pass_at_1 * 100:>6.1f}% | "
            f"{metrics.mean_reward:>8.4f} | "
            f"{metrics.syntax_valid_rate * 100:>6.1f}%"
        )
    print("-" * 60)
    print(
        f"{'GLOBAL':<10} | "
        f"{len(report.results):<6} | "
        f"{sum(1 for r in report.results if r.passed):<6} | "
        f"{report.global_pass_at_1 * 100:>6.1f}% | "
        f"{report.global_mean_reward:>8.4f} | "
        f"{'-':<8}"
    )
    print("=" * 60)

    # Export report
    output_path = PROJECT_ROOT / args.output
    exported = evaluator.export_report(report, output_path)
    print(f"\nReport successfully generated: {exported}")
    print(f"Report ID:    {report.report_id}")
    print(f"Dataset Hash: {report.dataset_hash}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
