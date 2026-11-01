"""Typed contracts, schemas, and protocol interfaces for the coding-training platform."""

from __future__ import annotations

from .attestation import AuditEvent, WorkerAttestation
from .checkpoints import CheckpointManifest
from .configs import (
    EnvironmentConfig,
    GenerationConfig,
    RLConfig,
    SandboxPolicy,
    SFTConfig,
)
from .evaluation import BaselineReport, SplitMetrics, TaskEvaluationResult
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
from .rl import (
    PolicyGradientStepResult,
    RLSpikeReport,
    RolloutCandidate,
    RolloutGroup,
)
from .tasks import DatasetManifest, Split, Task, TestBundleRef

__all__ = [
    "AuditEvent",
    "BaselineReport",
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
    "PolicyGradientStepResult",
    "RewardResult",
    "RewardVersion",
    "RLConfig",
    "RLSpikeReport",
    "RolloutCandidate",
    "RolloutGroup",
    "SandboxPolicy",
    "SFTConfig",
    "Split",
    "SplitMetrics",
    "Task",
    "TaskEvaluationResult",
    "TestBundleRef",
    "WorkerAttestation",
]
