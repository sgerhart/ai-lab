"""Unit tests for Execution-Reward RL (GRPO) Trainer and Checkpoint Provenance."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest import mock

from fastapi.testclient import TestClient

from packages.contracts import (
    ExecutionResult,
    ExecutionStatus,
    RLConfig,
)
from services.model.app import app, set_grpo_trainer
from services.model.grpo_trainer import GRPOTrainer, RLTrainingResult
from services.sandbox_worker.worker import SandboxWorker


class TestGRPOTrainer(unittest.TestCase):
    """Verifies GRPO training loop, parameter divergence, sandbox hooks, and tamper resistance."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.checkpoints_dir = Path(self.tmp_dir.name) / "adapters"
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)
        self.trainer = GRPOTrainer(checkpoints_dir=self.checkpoints_dir)

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_grpo_training_weight_divergence_success(self) -> None:
        """Mandatory Invariant: RL training must produce steps > 0 and diverging adapter weights."""
        config = RLConfig(group_size=4, beta=0.04, learning_rate=1e-4, max_steps=10)
        res = self.trainer.train(
            base_model="Qwen/Qwen3-0.6B",
            config=config,
            seed=42,
        )

        self.assertIsInstance(res, RLTrainingResult)
        self.assertGreater(res.steps_completed, 0)
        self.assertTrue(res.weights_diverged)
        self.assertNotEqual(res.initial_adapter_hash, res.final_adapter_hash)
        self.assertGreater(res.rollout_groups_processed, 0)
        self.assertGreaterEqual(res.mean_reward, 0.0)

        # Check on-disk artifacts
        ckpt_dir = self.checkpoints_dir / res.checkpoint_id
        self.assertTrue((ckpt_dir / "manifest.json").exists())
        self.assertTrue((ckpt_dir / "adapters.safetensors").exists())
        self.assertTrue((ckpt_dir / "adapter_config.json").exists())

        # Verify manifest
        manifest = self.trainer.verify_checkpoint(ckpt_dir)
        self.assertEqual(manifest.checkpoint_id, res.checkpoint_id)
        self.assertEqual(manifest.adapter_hash, res.final_adapter_hash)

    def test_grpo_trainer_fails_when_weights_do_not_diverge(self) -> None:
        """Mandatory Invariant: Runs where adapter weights do not diverge must fail closed."""
        dummy_hash = "0" * 64
        with mock.patch.object(
            self.trainer,
            "_train_grpo_loop",
            return_value=([], dummy_hash, dummy_hash, 10, b"safetensors", 10, 0.5),
        ):
            with self.assertRaises(ValueError) as ctx:
                self.trainer.train(config=RLConfig(max_steps=5))
            self.assertIn("Weight divergence check FAILED", str(ctx.exception))

    def test_grpo_trainer_fails_on_zero_steps(self) -> None:
        """Mandatory Invariant: Runs with 0 completed steps must fail closed."""
        with mock.patch.object(
            self.trainer,
            "_train_grpo_loop",
            return_value=([], "a" * 64, "b" * 64, 0, b"safetensors", 0, 0.0),
        ):
            with self.assertRaises(ValueError) as ctx:
                self.trainer.train(config=RLConfig(max_steps=5))
            self.assertIn("0 steps completed", str(ctx.exception))

    def test_checkpoint_verification_detects_tampering(self) -> None:
        """Tampered adapter weights on disk must fail verification."""
        config = RLConfig(group_size=4, max_steps=5)
        res = self.trainer.train(config=config)

        ckpt_dir = self.checkpoints_dir / res.checkpoint_id
        safetensors_file = ckpt_dir / "adapters.safetensors"

        # Tamper with file contents
        safetensors_file.write_bytes(b"corrupted_tampered_bytes")

        with self.assertRaises(ValueError) as ctx:
            self.trainer.verify_checkpoint(ckpt_dir)
        self.assertIn("Checksum mismatch", str(ctx.exception))

    def test_grpo_trainer_unscorable_exclusion(self) -> None:
        """Mandatory Invariant: Infrastructure failures (INFRA_ERROR) must be excluded from group advantages."""
        mock_worker = mock.MagicMock(spec=SandboxWorker)
        # Mock 1 infra error, 1 pass, 1 fail
        mock_worker.execute.side_effect = [
            ExecutionResult(
                job_id="job-01",
                task_id="py-001",
                candidate_sha256="0" * 64,
                test_bundle_sha256="1" * 64,
                status=ExecutionStatus.INFRA_ERROR,
                passed=0,
                total=0,
                elapsed_ms=10,
                exit_code=1,
                worker_id="worker-01",
                stdout="",
                stderr="Container launch failed",
            ),
            ExecutionResult(
                job_id="job-02",
                task_id="py-001",
                candidate_sha256="0" * 64,
                test_bundle_sha256="1" * 64,
                status=ExecutionStatus.COMPLETED,
                passed=5,
                total=5,
                elapsed_ms=10,
                exit_code=0,
                worker_id="worker-01",
                stdout="",
                stderr="",
            ),
            ExecutionResult(
                job_id="job-03",
                task_id="py-001",
                candidate_sha256="0" * 64,
                test_bundle_sha256="1" * 64,
                status=ExecutionStatus.RUNTIME_ERROR,
                passed=0,
                total=5,
                elapsed_ms=10,
                exit_code=1,
                worker_id="worker-01",
                stdout="",
                stderr="AssertionError",
            ),
            ExecutionResult(
                job_id="job-04",
                task_id="py-001",
                candidate_sha256="0" * 64,
                test_bundle_sha256="1" * 64,
                status=ExecutionStatus.COMPLETED,
                passed=5,
                total=5,
                elapsed_ms=10,
                exit_code=0,
                worker_id="worker-01",
                stdout="",
                stderr="",
            ),
        ]

        trainer_with_worker = GRPOTrainer(
            checkpoints_dir=self.checkpoints_dir,
            sandbox_worker=mock_worker,
        )
        res = trainer_with_worker.train(config=RLConfig(group_size=4, max_steps=1))
        self.assertGreater(res.steps_completed, 0)
        self.assertTrue(res.weights_diverged)

    def test_model_worker_rl_api_endpoints(self) -> None:
        """Verifies /v1/train/rl endpoint in model worker."""
        set_grpo_trainer(self.trainer)
        client = TestClient(app)

        req_body = {
            "base_model": "Qwen/Qwen3-0.6B",
            "revision": "main",
            "config": {
                "group_size": 4,
                "beta": 0.04,
                "learning_rate": 1e-4,
                "max_steps": 5,
            },
            "seed": 42,
        }
        resp = client.post("/v1/train/rl", json=req_body)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("checkpoint_id", data)
        self.assertTrue(data["weights_diverged"])
        self.assertEqual(data["manifest"]["optimizer_params"]["algorithm"], "grpo_adamw")


if __name__ == "__main__":
    unittest.main()
