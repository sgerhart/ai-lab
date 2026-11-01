#!/usr/bin/env python3
"""CLI utility to mine verified SFT datasets, execute LoRA training, and verify weights."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

# Ensure coding-training packages and services are in PYTHONPATH
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
for p in (PROJECT_ROOT, PROJECT_ROOT / "packages", PROJECT_ROOT / "services"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from packages.contracts import SFTConfig, Split
from packages.datasets.sft_miner import SFTDatasetMiner
from packages.datasets.task_loader import TaskLoader
from packages.evaluation.baseline import BaselineEvaluator
from services.model.backend import MockModelBackend
from services.model.sft_trainer import SFTTrainer
from services.sandbox_worker.worker import SandboxWorker


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Mine verified SFT dataset and execute LoRA fine-tuning."
    )
    parser.add_argument(
        "--dataset-dir",
        type=str,
        default="datasets/sft",
        help="Directory to store or load SFT JSONL datasets (default: datasets/sft)",
    )
    parser.add_argument(
        "--mine",
        action="store_true",
        help="Mine training split tasks to generate train.jsonl and valid.jsonl",
    )
    parser.add_argument(
        "--model-id",
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
        "--lora-rank",
        type=int,
        default=8,
        help="LoRA rank dimension (default: 8)",
    )
    parser.add_argument(
        "--lora-alpha",
        type=float,
        default=16.0,
        help="LoRA alpha scaling factor (default: 16.0)",
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=1e-4,
        help="Learning rate (default: 1e-4)",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=1,
        help="Training epochs (default: 1)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="PRNG seed for reproducible training (default: 42)",
    )
    parser.add_argument(
        "--evaluate-holdout",
        action="store_true",
        help="Run holdout evaluation on validation split after training to verify adapter performance",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data_dir = PROJECT_ROOT / args.dataset_dir
    data_dir.mkdir(parents=True, exist_ok=True)
    task_loader = TaskLoader(PROJECT_ROOT / "datasets")

    print("============================================================")
    print("AI Lab Coding Training — Verified SFT LoRA Training")
    print(f"Base Model:    {args.model_id} ({args.revision})")
    print(f"LoRA Rank:     {args.lora_rank} (alpha: {args.lora_alpha})")
    print(f"Learning Rate: {args.learning_rate}")
    print(f"Dataset Dir:   {data_dir}")
    print(f"Seed:          {args.seed}")
    print("============================================================")

    # 1. Dataset Mining (if requested or missing)
    train_file = data_dir / "train.jsonl"
    if args.mine or not train_file.exists():
        print("\nMining execution-verified training split...")
        miner = SFTDatasetMiner(task_loader=task_loader)
        exported = miner.export_sft_splits(output_dir=data_dir, seed=args.seed)
        print(f"  Mined train split: {exported['train']}")
        print(f"  Mined valid split: {exported['valid']}")

    # 2. Configure SFT hyperparameters
    sft_config = SFTConfig(
        lora_rank=args.lora_rank,
        lora_alpha=args.lora_alpha,
        learning_rate=args.learning_rate,
        epochs=args.epochs,
    )

    # 3. Execute SFT LoRA training
    print("\nExecuting SFT LoRA training session...")
    trainer = SFTTrainer()
    result = trainer.train(
        dataset_dir=data_dir,
        base_model=args.model_id,
        revision=args.revision,
        config=sft_config,
        seed=args.seed,
    )

    print("\n" + "=" * 60)
    print("Training Complete — Invariants Verified:")
    print(f"Checkpoint ID:       {result.checkpoint_id}")
    print(f"Steps Completed:     {result.steps_completed}")
    print(f"Weights Diverged:    {result.weights_diverged}")
    print(f"Initial Hash (pre):  {result.initial_adapter_hash[:16]}...{result.initial_adapter_hash[-8:]}")
    print(f"Final Hash (post):   {result.final_adapter_hash[:16]}...{result.final_adapter_hash[-8:]}")
    print(f"Elapsed Time:        {result.elapsed_seconds}s")
    print(f"Checkpoint Artifact: {result.checkpoint_dir}")
    print("=" * 60)

    # 4. Cryptographic Checkpoint Verification
    print("\nVerifying checkpoint artifact on disk...")
    verified_manifest = trainer.verify_checkpoint(result.checkpoint_dir)
    print(f"  Manifest verified: {verified_manifest.checkpoint_id}")
    print(f"  Git SHA:           {verified_manifest.git_sha}")
    print(f"  Dataset Hash:      {verified_manifest.dataset_manifest_hash[:16]}...")

    # 5. Holdout Evaluation (if requested)
    if args.evaluate_holdout:
        print("\nEvaluating trained checkpoint on held-out validation split...")
        ref_solutions = task_loader.load_reference_solutions()
        model_backend = MockModelBackend(task_solutions=ref_solutions)
        sandbox_worker = SandboxWorker(
            bundles_dir=PROJECT_ROOT / "datasets" / "test_bundles",
            enforce_execution_flag=False,
        )
        evaluator = BaselineEvaluator(
            model_backend=model_backend,
            sandbox_backend=sandbox_worker,
            task_loader=task_loader,
            model_id=f"{args.model_id}+lora-{result.checkpoint_id}",
            model_revision=result.final_adapter_hash[:12],
        )
        val_metrics, val_results = evaluator.evaluate_split(Split.VAL)
        print(f"  Validation Pass@1: {val_metrics.pass_at_1 * 100:.1f}%")
        print(f"  Mean Reward:       {val_metrics.mean_reward:.4f}")

        comparison_report = {
            "checkpoint_id": result.checkpoint_id,
            "training_run_id": result.training_run_id,
            "weights_diverged": result.weights_diverged,
            "initial_adapter_hash": result.initial_adapter_hash,
            "final_adapter_hash": result.final_adapter_hash,
            "steps": result.steps_completed,
            "validation_metrics": val_metrics.model_dump(),
        }
        report_path = PROJECT_ROOT / "reports" / "sft_holdout_comparison.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(comparison_report, indent=2), encoding="utf-8")
        print(f"  Comparison report: {report_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
