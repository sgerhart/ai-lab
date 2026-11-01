"""Unit tests for production SandboxWorker service and isolation lifecycle."""

from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest

from packages.contracts import (
    ExecutionRequest,
    ExecutionStatus,
    FailureClass,
    SandboxPolicy,
)
from packages.datasets.task_loader import TaskLoader
from services.sandbox_worker.jail import SubprocessJail
from services.sandbox_worker.worker import SandboxWorker


class TestSandboxWorker(unittest.TestCase):
    """Verifies sandbox worker protocol, safety gates, and bundle verification."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.base_dir = Path(__file__).resolve().parent.parent.parent
        cls.bundles_dir = cls.base_dir / "datasets" / "test_bundles"
        cls.loader = TaskLoader(root_dir=cls.base_dir / "datasets")
        cls.tasks = cls.loader.load_tasks()
        cls.solutions = cls.loader.load_reference_solutions()

    def setUp(self) -> None:
        # Isolated worker using SubprocessJail
        self.worker = SandboxWorker(
            worker_id="test-worker-01",
            bundles_dir=self.bundles_dir,
            jail=SubprocessJail(),
            enforce_execution_flag=False,  # Bypassed for authorized unit tests
        )

    def test_safety_switch_blocks_execution_by_default(self) -> None:
        """Mandatory Invariant: Execution MUST fail closed if execution_enabled=False."""
        strict_worker = SandboxWorker(
            worker_id="strict-worker",
            bundles_dir=self.bundles_dir,
            jail=SubprocessJail(),
            enforce_execution_flag=True,  # Strict mode
        )
        task = self.tasks[0]
        code = self.solutions[task.task_id]
        cand_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()

        req = ExecutionRequest(
            job_id="job-strict-01",
            task_id=task.task_id,
            candidate_code=code,
            candidate_sha256=cand_hash,
            test_bundle_ref=task.test_bundle_ref,
            test_bundle_sha256=task.test_bundle_sha256,
            runtime_image_digest="sha256:d8b2e1a4" * 8,
            sandbox_policy=SandboxPolicy(),
            deadline_epoch_ms=2000000000000,
        )

        res = strict_worker.execute(req)
        self.assertEqual(res.status, ExecutionStatus.INFRA_ERROR)
        self.assertTrue(res.is_infra_error)
        self.assertIn("EXECUTION_ENABLED=false", res.stderr)

    def test_candidate_hash_mismatch_fails_closed(self) -> None:
        """Tampered candidate code must be rejected before execution."""
        task = self.tasks[0]
        code = self.solutions[task.task_id]

        req = ExecutionRequest(
            job_id="job-mismatch-01",
            task_id=task.task_id,
            candidate_code=code,
            candidate_sha256="0" * 64,  # Intentionally corrupt digest
            test_bundle_ref=task.test_bundle_ref,
            test_bundle_sha256=task.test_bundle_sha256,
            runtime_image_digest="sha256:d8b2e1a4" * 8,
            sandbox_policy=SandboxPolicy(),
            deadline_epoch_ms=2000000000000,
        )

        res = self.worker.execute(req)
        self.assertEqual(res.status, ExecutionStatus.INFRA_ERROR)
        self.assertTrue(res.is_infra_error)
        self.assertIn("Candidate hash mismatch", res.stderr)

    def test_missing_test_bundle_produces_infra_error(self) -> None:
        """Missing test bundles must produce INFRA_ERROR (strictly scorable=False)."""
        task = self.tasks[0]
        code = self.solutions[task.task_id]
        cand_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()

        req = ExecutionRequest(
            job_id="job-missing-bundle-01",
            task_id=task.task_id,
            candidate_code=code,
            candidate_sha256=cand_hash,
            test_bundle_ref=task.test_bundle_ref,
            test_bundle_sha256="f" * 64,  # Non-existent bundle
            runtime_image_digest="sha256:d8b2e1a4" * 8,
            sandbox_policy=SandboxPolicy(),
            deadline_epoch_ms=2000000000000,
        )

        res = self.worker.execute(req)
        self.assertEqual(res.status, ExecutionStatus.INFRA_ERROR)
        self.assertEqual(res.failure_class, FailureClass.INFRA_BUNDLE_MISMATCH)
        self.assertTrue(res.is_infra_error)

    def test_corrupted_test_bundle_produces_infra_error(self) -> None:
        """Bundle content tampering must fail verification and produce INFRA_ERROR."""
        task = self.tasks[0]
        code = self.solutions[task.task_id]
        cand_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_bundles = Path(tmp_dir)
            corrupted_file = tmp_bundles / f"{task.test_bundle_sha256}.json"
            # Write invalid JSON or tampered content
            corrupted_file.write_text('{"entry_point": "bad", "test_cases": []}', encoding="utf-8")

            local_worker = SandboxWorker(
                bundles_dir=tmp_bundles,
                jail=SubprocessJail(),
                enforce_execution_flag=False,
            )

            req = ExecutionRequest(
                job_id="job-corrupt-01",
                task_id=task.task_id,
                candidate_code=code,
                candidate_sha256=cand_hash,
                test_bundle_ref=task.test_bundle_ref,
                test_bundle_sha256=task.test_bundle_sha256,
                runtime_image_digest="sha256:d8b2e1a4" * 8,
                sandbox_policy=SandboxPolicy(),
                deadline_epoch_ms=2000000000000,
            )

            res = local_worker.execute(req)
            self.assertEqual(res.status, ExecutionStatus.INFRA_ERROR)
            self.assertEqual(res.failure_class, FailureClass.INFRA_BUNDLE_MISMATCH)

    def test_successful_candidate_execution(self) -> None:
        """Valid reference solution must execute and pass all 20 test cases."""
        task = self.tasks[0]  # py-arr-001 (sum_array)
        code = self.solutions[task.task_id]
        cand_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()

        req = ExecutionRequest(
            job_id="job-pass-01",
            task_id=task.task_id,
            candidate_code=code,
            candidate_sha256=cand_hash,
            test_bundle_ref=task.test_bundle_ref,
            test_bundle_sha256=task.test_bundle_sha256,
            runtime_image_digest="sha256:d8b2e1a4" * 8,
            sandbox_policy=SandboxPolicy(wall_timeout_seconds=5.0),
            deadline_epoch_ms=2000000000000,
        )

        res = self.worker.execute(req)
        self.assertEqual(res.status, ExecutionStatus.COMPLETED)
        self.assertEqual(res.failure_class, FailureClass.NONE)
        self.assertEqual(res.passed, 20)
        self.assertEqual(res.total, 20)
        self.assertEqual(res.exit_code, 0)
        self.assertFalse(res.is_infra_error)

    def test_incorrect_candidate_execution(self) -> None:
        """Candidate returning wrong answer must produce RUNTIME_ERROR / ASSERTION_FAILED."""
        task = self.tasks[0]  # py-str-001
        wrong_code = "def reverse_string(s: str) -> str:\n    return 'wrong'\n"
        cand_hash = hashlib.sha256(wrong_code.encode("utf-8")).hexdigest()

        req = ExecutionRequest(
            job_id="job-fail-01",
            task_id=task.task_id,
            candidate_code=wrong_code,
            candidate_sha256=cand_hash,
            test_bundle_ref=task.test_bundle_ref,
            test_bundle_sha256=task.test_bundle_sha256,
            runtime_image_digest="sha256:d8b2e1a4" * 8,
            sandbox_policy=SandboxPolicy(),
            deadline_epoch_ms=2000000000000,
        )

        res = self.worker.execute(req)
        self.assertEqual(res.status, ExecutionStatus.RUNTIME_ERROR)
        self.assertEqual(res.failure_class, FailureClass.ASSERTION_FAILED)
        self.assertEqual(res.passed, 0)
        self.assertEqual(res.total, 20)
        self.assertFalse(res.is_infra_error)

    def test_worker_attestation_and_health(self) -> None:
        """Worker must produce verifiable attestation and healthy status."""
        att = self.worker.attest()
        self.assertEqual(att.worker_id, "test-worker-01")
        self.assertEqual(att.worker_role, "linux_sandbox_worker")
        self.assertTrue(att.egress_denied_verified)
        self.assertGreater(att.timestamp_epoch_ms, 0)

        health = self.worker.health()
        self.assertTrue(health.healthy)
        self.assertEqual(health.status, "ok")
        self.assertEqual(health.details["worker_id"], "test-worker-01")


if __name__ == "__main__":
    unittest.main()
