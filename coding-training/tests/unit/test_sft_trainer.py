"""Unit tests for SFT dataset mining, LoRA training, and weight verification."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from fastapi.testclient import TestClient

from packages.contracts import (
    CheckpointManifest,
    SFTConfig,
    Split,
)
from packages.datasets.sft_miner import SFTDatasetMiner
from packages.datasets.task_loader import TaskLoader
from services.model.app import app, set_sft_trainer
from services.model.sft_trainer import SFTTrainer, SFTTrainingResult


class TestSFTTrainer(unittest.TestCase):
    """Verifies SFT dataset mining, LoRA parameter divergence, and checkpoint verification."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.datasets_dir = Path(__file__).resolve().parents[2] / "datasets"
        cls.task_loader = TaskLoader(cls.datasets_dir)

    def test_sft_dataset_mining_strict_train_split(self) -> None:
        """Mandatory Invariant: Mined SFT datasets must contain ONLY tasks from Split.TRAIN."""
        miner = SFTDatasetMiner(task_loader=self.task_loader)
        records = miner.mine_training_dataset()

        self.assertEqual(len(records), 75)  # 75 train tasks
        val_tasks = {t.task_id for t in self.task_loader.get_tasks_by_split(Split.VAL)}
        test_tasks = {t.task_id for t in self.task_loader.get_tasks_by_split(Split.TEST)}

        for r in records:
            # Split check
            self.assertEqual(r["split"], "train")
            # Invariant: zero leak into validation or test holdouts
            self.assertNotIn(r["task_id"], val_tasks)
            self.assertNotIn(r["task_id"], test_tasks)
            self.assertTrue(len(r["candidate_sha256"]) == 64)
            self.assertIn("def ", r["completion"])

        # Test export
        with tempfile.TemporaryDirectory() as tmpdir:
            exported = miner.export_sft_splits(tmpdir, val_ratio=0.1, seed=42)
            self.assertTrue(exported["train"].exists())
            self.assertTrue(exported["valid"].exists())

            train_lines = [json.loads(line) for line in exported["train"].read_text().splitlines() if line.strip()]
            valid_lines = [json.loads(line) for line in exported["valid"].read_text().splitlines() if line.strip()]

            self.assertEqual(len(train_lines) + len(valid_lines), 75)
            for r in valid_lines:
                self.assertEqual(r["split"], "train")

    def test_sft_trainer_weight_divergence_success(self) -> None:
        """Mandatory Invariant: Training must produce steps > 0 and diverging adapter weights."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            data_dir = tmp_path / "data"
            ckpt_dir = tmp_path / "checkpoints"
            data_dir.mkdir()

            # Create dummy train.jsonl
            (data_dir / "train.jsonl").write_text(
                json.dumps({"prompt": "def add(a, b):", "completion": "def add(a, b): return a + b"}) + "\n"
            )

            trainer = SFTTrainer(checkpoints_dir=ckpt_dir, dry_run_fallback=True)
            res = trainer.train(
                dataset_dir=data_dir,
                base_model="Qwen/Qwen3-0.6B",
                revision="rev-001",
                config=SFTConfig(lora_rank=8, epochs=1),
                seed=42,
                training_run_id="test-run-01",
            )

            self.assertIsInstance(res, SFTTrainingResult)
            self.assertTrue(res.weights_diverged)
            self.assertNotEqual(res.initial_adapter_hash, res.final_adapter_hash)
            self.assertGreater(res.steps_completed, 0)
            self.assertGreater(len(res.loss_history), 0)

            # Verify files on disk
            checkpoint_path = Path(res.checkpoint_dir)
            self.assertTrue((checkpoint_path / "adapter_config.json").exists())
            self.assertTrue((checkpoint_path / "adapters.safetensors").exists())
            self.assertTrue((checkpoint_path / "manifest.json").exists())

            # Verify manifest
            manifest = trainer.verify_checkpoint(checkpoint_path)
            self.assertIsInstance(manifest, CheckpointManifest)
            self.assertEqual(manifest.checkpoint_id, res.checkpoint_id)
            self.assertEqual(manifest.adapter_hash, res.final_adapter_hash)
            self.assertNotEqual(manifest.initial_adapter_hash, manifest.adapter_hash)

    def test_sft_trainer_fails_when_weights_do_not_diverge(self) -> None:
        """Mandatory Invariant: Runs where adapter weights do not diverge must fail closed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            data_dir = tmp_path / "data"
            ckpt_dir = tmp_path / "checkpoints"
            data_dir.mkdir()
            (data_dir / "train.jsonl").write_text("{}\n")

            trainer = SFTTrainer(checkpoints_dir=ckpt_dir, dry_run_fallback=True)
            # Patch _train_simulated to return identical initial and final hash
            dummy_hash = "a" * 64
            trainer._train_simulated = lambda *args, **kwargs: ([], dummy_hash, dummy_hash, 10, b"weights")  # type: ignore

            with self.assertRaises(ValueError) as ctx:
                trainer.train(dataset_dir=data_dir)
            self.assertIn("Adapter weights did not diverge", str(ctx.exception))

    def test_checkpoint_verification_detects_tampering(self) -> None:
        """Tampered adapter weights on disk must fail verification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            data_dir = tmp_path / "data"
            ckpt_dir = tmp_path / "checkpoints"
            data_dir.mkdir()
            (data_dir / "train.jsonl").write_text("{}\n")

            trainer = SFTTrainer(checkpoints_dir=ckpt_dir, dry_run_fallback=True)
            res = trainer.train(dataset_dir=data_dir)

            # Corrupt the safetensors file
            safetensors_file = Path(res.checkpoint_dir) / "adapters.safetensors"
            safetensors_file.write_bytes(safetensors_file.read_bytes() + b"tamper_bytes")

            with self.assertRaises(ValueError) as ctx:
                trainer.verify_checkpoint(res.checkpoint_dir)
            self.assertIn("Checksum mismatch", str(ctx.exception))

    def test_model_worker_sft_api_endpoints(self) -> None:
        """Verifies /v1/train/sft, /v1/checkpoints, and /v1/checkpoints/{id} endpoints."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            data_dir = tmp_path / "data"
            ckpt_dir = tmp_path / "checkpoints"
            data_dir.mkdir()
            (data_dir / "train.jsonl").write_text("{}\n")

            trainer = SFTTrainer(checkpoints_dir=ckpt_dir, dry_run_fallback=True)
            set_sft_trainer(trainer)
            client = TestClient(app)

            # POST /v1/train/sft
            t_resp = client.post(
                "/v1/train/sft",
                json={
                    "dataset_dir": str(data_dir),
                    "base_model": "Qwen/Qwen3-0.6B",
                    "revision": "main",
                    "seed": 42,
                    "training_run_id": "api-run-01",
                },
            )
            self.assertEqual(t_resp.status_code, 200)
            t_data = t_resp.json()
            self.assertTrue(t_data["weights_diverged"])
            checkpoint_id = t_data["checkpoint_id"]

            # GET /v1/checkpoints
            c_resp = client.get("/v1/checkpoints")
            self.assertEqual(c_resp.status_code, 200)
            ckpts = c_resp.json()
            self.assertGreater(len(ckpts), 0)
            self.assertEqual(ckpts[0]["checkpoint_id"], checkpoint_id)

            # GET /v1/checkpoints/{id}
            s_resp = client.get(f"/v1/checkpoints/{checkpoint_id}")
            self.assertEqual(s_resp.status_code, 200)
            self.assertEqual(s_resp.json()["checkpoint_id"], checkpoint_id)

            # GET nonexistent checkpoint
            n_resp = client.get("/v1/checkpoints/nonexistent-id")
            self.assertEqual(n_resp.status_code, 404)
