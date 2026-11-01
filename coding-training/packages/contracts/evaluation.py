"""Evaluation contracts, metrics, and baseline report schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .executions import FailureClass
from .tasks import Split


class TaskEvaluationResult(BaseModel):
    """Result of evaluating a single task candidate."""
    task_id: str
    split: Split
    family_id: str
    model_id: str
    candidate_sha256: str
    passed: bool
    reward: float | None
    passed_tests: int = Field(ge=0)
    total_tests: int = Field(ge=0)
    syntax_valid: bool
    error_class: FailureClass = FailureClass.NONE
    latency_ms: int = Field(ge=0)
    prompt_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)


class SplitMetrics(BaseModel):
    """Aggregate evaluation statistics for a single split."""
    split: Split
    total_tasks: int = Field(ge=0)
    evaluated_tasks: int = Field(ge=0)
    passed_tasks: int = Field(ge=0)
    pass_at_1: float = Field(ge=0.0, le=1.0)
    mean_reward: float = Field(ge=0.0, le=1.0)
    syntax_valid_count: int = Field(ge=0)
    syntax_valid_rate: float = Field(ge=0.0, le=1.0)
    compile_errors: int = Field(ge=0)
    runtime_errors: int = Field(ge=0)
    timeouts: int = Field(ge=0)
    infra_errors: int = Field(ge=0)


class BaselineReport(BaseModel):
    """Reproducible baseline holdout evaluation report."""
    report_id: str
    created_at: str
    model_id: str
    model_revision: str
    dataset_hash: str
    splits: dict[str, SplitMetrics]
    global_pass_at_1: float = Field(ge=0.0, le=1.0)
    global_mean_reward: float = Field(ge=0.0, le=1.0)
    results: list[TaskEvaluationResult]
    metadata: dict[str, object] = Field(default_factory=dict)
