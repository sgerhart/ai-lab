"""Sandbox worker backend interface and mock implementation."""

from __future__ import annotations

import hashlib
from typing import Protocol

from packages.contracts import (
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
    FailureClass,
    HealthStatus,
    WorkerAttestation,
)


class SandboxBackend(Protocol):
    """Protocol for isolated sandbox workers."""

    def execute(self, request: ExecutionRequest) -> ExecutionResult: ...

    def attest(self) -> WorkerAttestation: ...

    def health(self) -> HealthStatus: ...


class MockSandboxBackend:
    """Safe mock sandbox backend for unit tests.
    
    Simulates code execution without opening network connections or running hostile processes.
    """

    def __init__(
        self,
        worker_id: str = "mock-worker-01",
        default_status: ExecutionStatus = ExecutionStatus.COMPLETED,
        default_passed: int = 10,
        default_total: int = 10,
    ):
        self.worker_id = worker_id
        self.default_status = default_status
        self.default_passed = default_passed
        self.default_total = default_total

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        # Check bundle sha256 invariant
        if request.test_bundle_sha256.startswith("0000000000000000"):
            return ExecutionResult(
                job_id=request.job_id,
                task_id=request.task_id,
                candidate_sha256=request.candidate_sha256,
                test_bundle_sha256=request.test_bundle_sha256,
                status=ExecutionStatus.INFRA_ERROR,
                passed=0,
                total=0,
                elapsed_ms=5,
                exit_code=1,
                stderr="Test bundle checksum mismatch: bundle corrupted",
                sandbox_policy_version=request.sandbox_policy.sandbox_policy_version,
                worker_id=self.worker_id,
                failure_class=FailureClass.INFRA_BUNDLE_MISMATCH,
            )

        # Basic check for candidate code syntax
        try:
            compile(request.candidate_code, "<candidate>", "exec")
        except SyntaxError as err:
            return ExecutionResult(
                job_id=request.job_id,
                task_id=request.task_id,
                candidate_sha256=request.candidate_sha256,
                test_bundle_sha256=request.test_bundle_sha256,
                status=ExecutionStatus.COMPILE_ERROR,
                passed=0,
                total=self.default_total,
                elapsed_ms=10,
                exit_code=1,
                stderr=f"SyntaxError: {err}",
                sandbox_policy_version=request.sandbox_policy.sandbox_policy_version,
                worker_id=self.worker_id,
                failure_class=FailureClass.SYNTAX_ERROR,
            )

        return ExecutionResult(
            job_id=request.job_id,
            task_id=request.task_id,
            candidate_sha256=request.candidate_sha256,
            test_bundle_sha256=request.test_bundle_sha256,
            status=self.default_status,
            passed=self.default_passed,
            total=self.default_total,
            elapsed_ms=85,
            exit_code=0 if self.default_status == ExecutionStatus.COMPLETED else 1,
            stdout="All tests passed successfully." if self.default_passed == self.default_total else "1 test failed.",
            stderr="",
            sandbox_policy_version=request.sandbox_policy.sandbox_policy_version,
            worker_id=self.worker_id,
            failure_class=FailureClass.NONE if self.default_passed == self.default_total else FailureClass.ASSERTION_FAILED,
        )

    def attest(self) -> WorkerAttestation:
        dummy_digest = hashlib.sha256(b"mock-image-v1").hexdigest()
        return WorkerAttestation(
            worker_id=self.worker_id,
            worker_role="mock_sandbox_worker",
            runtime_image_digest=dummy_digest,
            sandbox_policy_version="sandbox-v1",
            vm_identity="mock-vm-local",
            timestamp_epoch_ms=1700000000000,
            egress_denied_verified=True,
        )

    def health(self) -> HealthStatus:
        return HealthStatus(healthy=True, status="ok", details={"worker_id": self.worker_id})
