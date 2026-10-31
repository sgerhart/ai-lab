"""Model interfaces, capabilities, and generation result contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ModelCapabilities(BaseModel):
    """Capabilities reported by the active ModelBackend."""
    supports_inference: bool = True
    supports_sft: bool = True
    supports_lora: bool = True
    supports_qlora: bool = False
    supports_grpo: bool = False
    supports_logprobs: bool = False
    device_arch: str = Field(default="apple_silicon")


class HealthStatus(BaseModel):
    """Health check response for internal services."""
    healthy: bool
    status: str = "ok"
    details: dict[str, object] = Field(default_factory=dict)


class ModelConfig(BaseModel):
    """Model identity, revision, and architecture settings."""
    model_id: str = Field(description="Model identifier, e.g. Qwen/Qwen3-0.6B")
    model_revision: str = Field(description="Exact git commit hash of the model weights")
    tokenizer_revision: str = Field(description="Exact git commit hash of the tokenizer")
    architecture: str = Field(default="qwen3")
    quantization: str | None = Field(default=None)


class GenerationResult(BaseModel):
    """Structured output from a model generation call."""
    raw_text: str
    extracted_code: str
    syntax_valid: bool
    prompt_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)
    latency_ms: int = Field(ge=0)
    model_version: str
    stop_reason: str = "stop"
