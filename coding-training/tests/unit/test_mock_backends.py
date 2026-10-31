"""Unit tests for mock model and sandbox worker backends."""

from __future__ import annotations

import unittest

from packages.contracts import (
    ExecutionRequest,
    ExecutionStatus,
    FailureClass,
    GenerationConfig,
    SandboxPolicy,
)
from services.model import MockModelBackend, extract_python_code
from services.sandbox_worker import MockSandboxBackend


class TestMockBackends(unittest.TestCase):
    """Verifies that mock services implement typed protocols and behave deterministically."""

    def test_extract_python_code_markdown_fence(self) -> None:
        raw = "Here is the code:\n```python\ndef add(a, b):\n    return a + b\n```\nHope that helps!"
        extracted, valid = extract_python_code(raw)
        self.assertTrue(valid)
        self.assertEqual(extracted, "def add(a, b):\n    return a + b")

    def test_extract_python_code_syntax_error(self) -> None:
        raw = "```python\ndef broken(\n    return 42\n```"
        extracted, valid = extract_python_code(raw)
        self.assertFalse(valid)
        self.assertIn("def broken(", extracted)

    def test_mock_model_backend_lifecycle(self) -> None:
        backend = MockModelBackend()
        backend.load("Qwen/Qwen3-0.6B", "rev-12345")
        
        cfg = GenerationConfig(temperature=0.2, seed=42)
        res = backend.generate("def hello():", seed=42, config=cfg)
        
        self.assertTrue(res.syntax_valid)
        self.assertIn("def solution", res.extracted_code)
        self.assertEqual(res.model_version, "Qwen/Qwen3-0.6B@rev-12345")
        self.assertTrue(backend.capabilities().supports_inference)
        self.assertTrue(backend.health().healthy)

    def test_mock_sandbox_backend_execution(self) -> None:
        backend = MockSandboxBackend(worker_id="test-worker")
        dummy_hash = "1" * 64

        # Valid candidate code
        req = ExecutionRequest(
            job_id="job-01",
            task_id="task-01",
            candidate_code="def solution():\n    return 42\n",
            candidate_sha256=dummy_hash,
            test_bundle_ref="bundle-01",
            test_bundle_sha256=dummy_hash,
            runtime_image_digest="digest-01",
            sandbox_policy=SandboxPolicy(),
            deadline_epoch_ms=1700000000000,
        )
        res = backend.execute(req)
        self.assertEqual(res.status, ExecutionStatus.COMPLETED)
        self.assertEqual(res.passed, 10)
        self.assertEqual(res.total, 10)
        self.assertFalse(res.is_infra_error)

        # Candidate code with syntax error
        bad_req = ExecutionRequest(
            job_id="job-02",
            task_id="task-01",
            candidate_code="def broken(:\n    return\n",
            candidate_sha256=dummy_hash,
            test_bundle_ref="bundle-01",
            test_bundle_sha256=dummy_hash,
            runtime_image_digest="digest-01",
            sandbox_policy=SandboxPolicy(),
            deadline_epoch_ms=1700000000000,
        )
        bad_res = backend.execute(bad_req)
        self.assertEqual(bad_res.status, ExecutionStatus.COMPILE_ERROR)
        self.assertEqual(bad_res.failure_class, FailureClass.SYNTAX_ERROR)
        self.assertFalse(bad_res.is_infra_error)

        # Corrupted bundle hash triggers infra error
        corrupt_hash = "0000000000000000" + ("a" * 48)
        corrupt_req = ExecutionRequest(
            job_id="job-03",
            task_id="task-01",
            candidate_code="def solution(): return 1",
            candidate_sha256=dummy_hash,
            test_bundle_ref="bundle-01",
            test_bundle_sha256=corrupt_hash,
            runtime_image_digest="digest-01",
            sandbox_policy=SandboxPolicy(),
            deadline_epoch_ms=1700000000000,
        )
        corrupt_res = backend.execute(corrupt_req)
        self.assertEqual(corrupt_res.status, ExecutionStatus.INFRA_ERROR)
        self.assertEqual(corrupt_res.failure_class, FailureClass.INFRA_BUNDLE_MISMATCH)
        self.assertTrue(corrupt_res.is_infra_error)

    def test_mock_sandbox_attestation(self) -> None:
        backend = MockSandboxBackend(worker_id="test-worker")
        att = backend.attest()
        self.assertEqual(att.worker_id, "test-worker")
        self.assertTrue(att.egress_denied_verified)
        self.assertEqual(len(att.runtime_image_digest), 64)


if __name__ == "__main__":
    unittest.main()
