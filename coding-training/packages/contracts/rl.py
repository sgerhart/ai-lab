"""Reinforcement learning (GRPO / PPO) rollout and gradient spike contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RolloutCandidate(BaseModel):
    """A single sampled rollout completion with execution reward and token logprobs."""
    candidate_id: str
    task_id: str
    code: str
    tokens: list[int]
    logprobs: list[float]
    ref_logprobs: list[float]
    reward: float = Field(ge=0.0, le=1.0)


class RolloutGroup(BaseModel):
    """Group of G candidate rollouts for a single prompt."""
    group_id: str
    task_id: str
    prompt: str
    candidates: list[RolloutCandidate]
    advantages: list[float] = Field(default_factory=list)


class PolicyGradientStepResult(BaseModel):
    """Result of an on-policy policy gradient optimizer update step."""
    step: int = Field(ge=0)
    policy_loss: float
    kl_penalty: float
    total_loss: float
    mean_advantage: float
    gradient_norm: float = Field(ge=0.0)
    weights_diverged: bool
    initial_param_hash: str = Field(min_length=64, max_length=64)
    updated_param_hash: str = Field(min_length=64, max_length=64)


class RLSpikeReport(BaseModel):
    """Comprehensive findings report from the Apple Silicon RL compatibility spike."""
    spike_id: str
    timestamp_utc: str
    framework: str
    device_arch: str
    gradient_step_verified: bool
    loss_finite: bool
    advantages_normalized: bool
    group_size: int = Field(ge=2)
    step_result: PolicyGradientStepResult
    findings: list[str]
    recommendation: str
