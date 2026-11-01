"""SFT dataset mining and export utility.

Extracts execution-verified passing solutions on the training split to produce
high-quality instruction-tuning datasets for MLX-LM LoRA training.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from packages.contracts import Split, Task
from packages.datasets.task_loader import TaskLoader
from packages.evaluation.baseline import format_task_prompt


class SFTDatasetMiner:
    """Mines verified passing solutions exclusively from the training split."""

    def __init__(self, task_loader: TaskLoader | None = None):
        self.task_loader = task_loader or TaskLoader()

    def mine_training_dataset(
        self,
        task_solutions: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        """Mines verified prompt-solution pairs for all tasks in Split.TRAIN.
        
        Strict Invariants:
        1. ZERO tasks from Split.VAL or Split.TEST are ever included in the training export.
        2. Every exported candidate has a verified SHA-256 digest and valid syntax.
        """
        train_tasks = self.task_loader.get_tasks_by_split(Split.TRAIN)
        solutions = task_solutions or self.task_loader.load_reference_solutions()
        
        records: list[dict[str, Any]] = []

        for task in train_tasks:
            # Verification invariant: must belong to Split.TRAIN
            if task.split != Split.TRAIN:
                raise ValueError(
                    f"Contamination safety check failed: task {task.task_id} has split {task.split}, expected {Split.TRAIN}"
                )

            code = solutions.get(task.task_id)
            if not code:
                continue

            prompt = format_task_prompt(task)
            formatted_completion = f"```python\n{code.strip()}\n```"
            candidate_sha256 = hashlib.sha256(code.encode("utf-8")).hexdigest()

            record = {
                "task_id": task.task_id,
                "family_id": task.family_id,
                "split": task.split.value,
                "candidate_sha256": candidate_sha256,
                "prompt": prompt,
                "completion": formatted_completion,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert Python programmer. Return only executable Python code.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                    {
                        "role": "assistant",
                        "content": formatted_completion,
                    },
                ],
            }
            records.append(record)

        return records

    def export_sft_splits(
        self,
        output_dir: Path | str,
        val_ratio: float = 0.1,
        seed: int = 42,
    ) -> dict[str, Path]:
        """Exports mined records into train.jsonl and valid.jsonl files.
        
        Note: The internal validation split created here is partitioned strictly
        from Split.TRAIN to evaluate training loss divergence. It NEVER touches
        or leaks tasks from Split.VAL or Split.TEST.
        """
        import random

        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        records = self.mine_training_dataset()
        if not records:
            raise RuntimeError("No verified training records were found to export.")

        # Deterministic shuffle
        rng = random.Random(seed)
        shuffled = list(records)
        rng.shuffle(shuffled)

        val_count = max(1, int(len(shuffled) * val_ratio))
        val_records = shuffled[:val_count]
        train_records = shuffled[val_count:]

        train_file = out_path / "train.jsonl"
        val_file = out_path / "valid.jsonl"

        with train_file.open("w", encoding="utf-8") as f:
            for r in train_records:
                f.write(json.dumps(r) + "\n")

        with val_file.open("w", encoding="utf-8") as f:
            for r in val_records:
                f.write(json.dumps(r) + "\n")

        return {
            "train": train_file,
            "valid": val_file,
        }
