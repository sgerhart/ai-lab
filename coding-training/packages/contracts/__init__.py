"""Typed contracts, schemas, and protocol interfaces for the coding-training platform."""

from __future__ import annotations

from .attestation import WorkerAttestation
from .checkpoints import CheckpointManifest
from .configs import (
    EnvironmentConfig,
    GenerationConfig,
    RLConfig,
    SandboxPolicy,
    SFTConfig,
)
from .executions import (
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
    FailureClass,
)
from .models import (
    GenerationResult,
    HealthStatus,
    ModelCapabilities,
    ModelConfig,
)
from .rewards import RewardResult, RewardVersion
from .tasks import DatasetManifest, Split, Task, TestBundleRef

__all__ = [
    "CheckpointManifest",
    "DatasetManifest",
    "EnvironmentConfig",
    "ExecutionRequest",
    "ExecutionResult",
    "ExecutionStatus",
    "FailureClass",
    "GenerationConfig",
    "GenerationResult",
    "HealthStatus",
    "ModelCapabilities",
    "ModelConfig",
    "RewardResult",
    "RewardVersion",
    "RLConfig",
    "SandboxPolicy",
    "SFTConfig",
    "Split",
    "Task",
    "TestBundleRef",
    "WorkerAttestation",
]
