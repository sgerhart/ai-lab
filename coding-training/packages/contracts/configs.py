"""Configuration schemas and safe defaults."""

from __future__ import annotations

from pydantic import BaseModel, Field


class EnvironmentConfig(BaseModel):
    """Runtime environment switches and service locations.
    
    Default values strictly enforce safe dry-run modes.
    """
    execution_enabled: bool = Field(
        default=False,
        description="Whether candidate code may be sent to the sandbox worker.",
    )
    training_enabled: bool = Field(
        default=False,
        description="Whether parameter training jobs may run on the compute host.",
    )
    rl_enabled: bool = Field(
        default=False,
        description="Whether reinforcement learning updates are enabled.",
    )
    sandbox_network_policy: str = Field(
        default="deny_all",
        description="Egress policy for sandbox execution ('deny_all').",
    )
    model_downloads_enabled: bool = Field(
        default=False,
        description="Whether unreviewed weight downloads are permitted.",
    )
    max_execution_parallelism: int = Field(
        default=1,
        ge=1,
        le=8,
        description="Maximum concurrent executions on the sandbox worker.",
    )
    max_generations_per_task: int = Field(
        default=4,
        ge=1,
        le=32,
        description="Default candidate sample count per task.",
    )
    default_reward_version: str = Field(
        default="reward-v1",
        description="Default reward scoring algorithm version.",
    )
    controller_bind: str = Field(
        default="127.0.0.1",
        description="Listen address for the controller API.",
    )
    controller_port: int = Field(
        default=8092,
        ge=1024,
        le=65535,
        description="Port for the controller API.",
    )
    model_worker_url: str = Field(
        default="http://mac-studio:8090",
        description="Endpoint URL for the ModelWorker service.",
    )
    sandbox_worker_url: str = Field(
        default="http://192.168.99.10:8095",
        description="Endpoint URL for the SandboxWorker service.",
    )


class GenerationConfig(BaseModel):
    """Decoding and sampling configuration for code generation."""
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    top_p: float = Field(default=0.95, ge=0.0, le=1.0)
    max_prompt_tokens: int = Field(default=2048, ge=64, le=8192)
    max_completion_tokens: int = Field(default=1024, ge=32, le=4096)
    stop_tokens: list[str] = Field(default_factory=lambda: ["<|endoftext|>", "```", "\nclass ", "\n# Test"])
    seed: int = Field(default=42)


class SandboxPolicy(BaseModel):
    """Resource constraints and jail parameters for disposable sandbox runs."""
    sandbox_policy_version: str = Field(default="sandbox-v1")
    cpu_limit: float = Field(default=1.0, ge=0.1, le=4.0)
    memory_limit_mb: int = Field(default=512, ge=64, le=4096)
    pids_limit: int = Field(default=64, ge=8, le=256)
    wall_timeout_seconds: float = Field(default=10.0, ge=1.0, le=60.0)
    stdout_limit_bytes: int = Field(default=1048576, ge=1024, le=10485760)
    stderr_limit_bytes: int = Field(default=1048576, ge=1024, le=10485760)
    network_enabled: bool = Field(default=False)


class SFTConfig(BaseModel):
    """Hyperparameters for LoRA/QLoRA supervised fine-tuning."""
    lora_rank: int = Field(default=8, ge=1, le=128)
    lora_alpha: float = Field(default=16.0, ge=1.0, le=256.0)
    learning_rate: float = Field(default=1e-4, ge=1e-6, le=1e-2)
    batch_size: int = Field(default=2, ge=1, le=32)
    epochs: int = Field(default=1, ge=1, le=10)
    max_seq_len: int = Field(default=2048, ge=128, le=8192)
    checkpoint_every_steps: int = Field(default=50, ge=1)


class RLConfig(BaseModel):
    """Hyperparameters for on-policy execution-reward reinforcement learning (GRPO)."""
    group_size: int = Field(default=4, ge=2, le=16, description="Rollouts per prompt (G)")
    beta: float = Field(default=0.04, ge=0.0, le=1.0, description="KL divergence penalty")
    learning_rate: float = Field(default=5e-6, ge=1e-7, le=1e-3)
    clip_range: float = Field(default=0.2, ge=0.05, le=0.5)
    max_steps: int = Field(default=100, ge=1)
    checkpoint_every_steps: int = Field(default=20, ge=1)
