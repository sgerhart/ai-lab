"""Execution request, result, and status schemas."""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field

from .configs import SandboxPolicy


class ExecutionStatus(str, Enum):
    """Terminal outcome of an execution attempt."""
    COMPLETED = "completed"
    TIMED_OUT = "timed_out"
    COMPILE_ERROR = "compile_error"
    RUNTIME_ERROR = "runtime_error"
    INFRA_ERROR = "infra_error"
    CANCELLED = "cancelled"


class FailureClass(str, Enum):
    """Categorized root cause of failure."""
    NONE = "none"
    SYNTAX_ERROR = "syntax_error"
    ASSERTION_FAILED = "assertion_failed"
    TIMEOUT = "timeout"
    MEMORY_EXCEEDED = "memory_exceeded"
    PROCESS_LIMIT_EXCEEDED = "process_limit_exceeded"
    OUTPUT_TRUNCATED = "output_truncated"
    FORBIDDEN_CALL = "forbidden_call"
    # Infrastructure failures (strictly not candidate's fault)
    INFRA_WORKER_DOWN = "infra_worker_down"
    INFRA_BUNDLE_MISMATCH = "infra_bundle_mismatch"
    INFRA_TIMEOUT = "infra_timeout"
    INFRA_UNEXPECTED = "infra_unexpected"


class ExecutionRequest(BaseModel):
    """Job payload sent to the sandbox worker."""
    schema_version: str = Field(default="1.0")
    job_id: str
    task_id: str
    candidate_code: str
    candidate_sha256: str = Field(min_length=64, max_length=64)
    test_bundle_ref: str
    test_bundle_sha256: str = Field(min_length=64, max_length=64)
    runtime_image_digest: str = Field(description="Pinned OCI digest of the execution image")
    sandbox_policy: SandboxPolicy = Field(default_factory=SandboxPolicy)
    deadline_epoch_ms: int


class ExecutionResult(BaseModel):
    """Immutable report returned by the sandbox worker."""
    schema_version: str = Field(default="1.0")
    job_id: str
    task_id: str
    candidate_sha256: str = Field(min_length=64, max_length=64)
    test_bundle_sha256: str = Field(min_length=64, max_length=64)
    status: ExecutionStatus
    passed: int = Field(ge=0)
    total: int = Field(ge=0)
    elapsed_ms: int = Field(ge=0)
    exit_code: int
    stdout: str = Field(default="")
    stderr: str = Field(default="")
    stdout_truncated: bool = Field(default=False)
    stderr_truncated: bool = Field(default=False)
    sandbox_policy_version: str = Field(default="sandbox-v1")
    worker_id: str
    failure_class: FailureClass = Field(default=FailureClass.NONE)

    @property
    def is_infra_error(self) -> bool:
        """Returns True if the failure was infrastructure-related, not candidate code."""
        return self.status == ExecutionStatus.INFRA_ERROR or self.failure_class.value.startswith("infra_")
