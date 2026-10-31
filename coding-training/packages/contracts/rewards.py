"""Deterministic reward calculation schemas."""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field

from .executions import FailureClass


class RewardVersion(str, Enum):
    """Scoring algorithm version."""
    V1 = "reward-v1"


class RewardResult(BaseModel):
    """Scored evaluation result for a candidate execution."""
    schema_version: str = Field(default="1.0")
    job_id: str
    candidate_sha256: str = Field(min_length=64, max_length=64)
    test_bundle_sha256: str = Field(min_length=64, max_length=64)
    reward: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Normalized reward score clamped [0.0, 1.0]. Null when unscorable.",
    )
    is_scorable: bool = Field(description="True if run completed validly to produce a score")
    unscorable_reason: str | None = Field(
        default=None,
        description="Reason if the run could not be scored (e.g. infrastructure error)",
    )
    passed: int = Field(ge=0)
    total: int = Field(ge=0)
    scoring_version: str = Field(default="reward-v1")
    failure_class: FailureClass = Field(default=FailureClass.NONE)
