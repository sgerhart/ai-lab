"""Checkpoint metadata and cryptographic provenance contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CheckpointManifest(BaseModel):
    """Immutable provenance manifest for a trained adapter checkpoint."""
    checkpoint_id: str
    training_run_id: str
    step: int = Field(ge=0)
    adapter_hash: str = Field(min_length=64, max_length=64, description="SHA-256 of adapter safetensors")
    base_model_revision: str
    tokenizer_revision: str
    dataset_manifest_hash: str = Field(min_length=64, max_length=64)
    git_sha: str
    seed: int
    optimizer_params: dict[str, object] = Field(default_factory=dict)
    initial_adapter_hash: str = Field(
        min_length=64,
        max_length=64,
        description="Adapter hash before training steps, proving weight divergence",
    )
    created_at_utc: str
