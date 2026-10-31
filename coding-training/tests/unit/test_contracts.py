"""Unit tests for contract schemas and validation."""

from __future__ import annotations

import unittest
from pydantic import ValidationError

from packages.contracts import (
    CheckpointManifest,
    DatasetManifest,
    EnvironmentConfig,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
    FailureClass,
    GenerationConfig,
    RewardResult,
    SandboxPolicy,
    Split,
    Task,
    WorkerAttestation,
)


class TestContracts(unittest.TestCase):
    """Verifies that all Pydantic contracts enforce strict types and invariants."""

    def test_environment_config_safe_defaults(self) -> None:
        cfg = EnvironmentConfig()
        self.assertFalse(cfg.execution_enabled)
        self.assertFalse(cfg.training_enabled)
        self.assertFalse(cfg.rl_enabled)
        self.assertFalse(cfg.model_downloads_enabled)
        self.assertEqual(cfg.sandbox_network_policy, "deny_all")
        self.assertEqual(cfg.max_execution_parallelism, 1)

    def test_dataset_manifest_and_policy(self) -> None:
        dummy_hash = "c" * 64
        manifest = DatasetManifest(
            dataset_id="ds-001",
            name="core-python-tasks",
            version="1.0",
            manifest_hash=dummy_hash,
            tasks_count=100,
            splits={"train": 70, "val": 15, "test": 15},
        )
        self.assertEqual(manifest.tasks_count, 100)

        policy = SandboxPolicy(cpu_limit=2.0, memory_limit_mb=1024)
        self.assertEqual(policy.cpu_limit, 2.0)
        self.assertFalse(policy.network_enabled)

    def test_generation_config_and_reward_result(self) -> None:
        gen_cfg = GenerationConfig(temperature=0.7, seed=99)
        self.assertEqual(gen_cfg.temperature, 0.7)

        dummy_hash = "d" * 64
        reward = RewardResult(
            job_id="j-01",
            candidate_sha256=dummy_hash,
            test_bundle_sha256=dummy_hash,
            reward=0.85,
            is_scorable=True,
            passed=17,
            total=20,
        )
        self.assertTrue(reward.is_scorable)
        self.assertEqual(reward.passed, 17)

    def test_checkpoint_manifest(self) -> None:
        h1 = "1" * 64
        h2 = "2" * 64
        h3 = "3" * 64
        ckpt = CheckpointManifest(
            checkpoint_id="ckpt-001",
            training_run_id="run-001",
            step=100,
            adapter_hash=h1,
            base_model_revision="rev-base",
            tokenizer_revision="rev-tok",
            dataset_manifest_hash=h2,
            git_sha="git-sha-test",
            seed=42,
            initial_adapter_hash=h3,
            created_at_utc="2026-10-30T20:00:00Z",
        )
        self.assertEqual(ckpt.step, 100)
        self.assertNotEqual(ckpt.adapter_hash, ckpt.initial_adapter_hash)

    def test_task_schema_validation(self) -> None:
        dummy_hash = "a" * 64
        task = Task(
            task_id="py-fib-001",
            prompt="def fib(n: int) -> int:",
            function_contract="fib(n: int) -> int",
            difficulty="easy",
            license="Apache-2.0",
            source_provenance="synthetic-verified",
            split=Split.TRAIN,
            family_id="fibonacci",
            test_bundle_ref="bundle-fib-001",
            test_bundle_sha256=dummy_hash,
            tags=["recursion", "math"],
        )
        self.assertEqual(task.task_id, "py-fib-001")
        self.assertEqual(task.split, Split.TRAIN)
        self.assertEqual(len(task.test_bundle_sha256), 64)

        # Invalid hash length should raise ValidationError
        with self.assertRaises(ValidationError):
            Task(
                task_id="bad-task",
                prompt="test",
                function_contract="test",
                difficulty="easy",
                license="MIT",
                source_provenance="test",
                split=Split.TRAIN,
                family_id="test",
                test_bundle_ref="bundle-1",
                test_bundle_sha256="short_hash",
            )

    def test_execution_request_and_result(self) -> None:
        dummy_hash = "b" * 64
        req = ExecutionRequest(
            job_id="job-001",
            task_id="py-fib-001",
            candidate_code="def fib(n): return n",
            candidate_sha256=dummy_hash,
            test_bundle_ref="bundle-1",
            test_bundle_sha256=dummy_hash,
            runtime_image_digest="sha256:" + ("c" * 64),
            deadline_epoch_ms=1700000000000,
        )
        self.assertEqual(req.job_id, "job-001")

        res = ExecutionResult(
            job_id="job-001",
            task_id="py-fib-001",
            candidate_sha256=dummy_hash,
            test_bundle_sha256=dummy_hash,
            status=ExecutionStatus.COMPLETED,
            passed=5,
            total=10,
            elapsed_ms=120,
            exit_code=0,
            worker_id="worker-01",
            failure_class=FailureClass.ASSERTION_FAILED,
        )
        self.assertFalse(res.is_infra_error)
        self.assertEqual(res.passed, 5)

        infra_res = ExecutionResult(
            job_id="job-002",
            task_id="py-fib-001",
            candidate_sha256=dummy_hash,
            test_bundle_sha256=dummy_hash,
            status=ExecutionStatus.INFRA_ERROR,
            passed=0,
            total=0,
            elapsed_ms=10,
            exit_code=1,
            worker_id="worker-01",
            failure_class=FailureClass.INFRA_WORKER_DOWN,
        )
        self.assertTrue(infra_res.is_infra_error)

    def test_worker_attestation(self) -> None:
        att = WorkerAttestation(
            worker_id="worker-01",
            runtime_image_digest="d" * 64,
            sandbox_policy_version="sandbox-v1",
            vm_identity="vm-uuid-1234",
            timestamp_epoch_ms=1700000000000,
            egress_denied_verified=True,
        )
        self.assertEqual(att.worker_role, "sandbox_worker")
        self.assertTrue(att.egress_denied_verified)


if __name__ == "__main__":
    unittest.main()
