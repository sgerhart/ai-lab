"""FastAPI application for the ModelWorker service on mac-studio."""

from __future__ import annotations

import os
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException

from packages.contracts import (
    CheckpointManifest,
    GenerationConfig,
    GenerationResult,
    HealthStatus,
    ModelCapabilities,
    RLConfig,
    SFTConfig,
)
from services.model.backend import MLXModelBackend, MockModelBackend, ModelBackend
from services.model.grpo_trainer import GRPOTrainer, RLTrainingResult
from services.model.sft_trainer import SFTTrainer, SFTTrainingResult

app = FastAPI(
    title="Coding Training Model Worker",
    version="1.0.0",
    description="Mac Studio model serving, code generation, and fine-tuning service.",
)

# Global model backend and trainer instances
_model_backend: ModelBackend | None = None
_sft_trainer: SFTTrainer | None = None
_grpo_trainer: GRPOTrainer | None = None


def get_grpo_trainer() -> GRPOTrainer:
    global _grpo_trainer
    if _grpo_trainer is None:
        _grpo_trainer = GRPOTrainer()
    return _grpo_trainer


def set_grpo_trainer(trainer: GRPOTrainer) -> None:
    global _grpo_trainer
    _grpo_trainer = trainer


def get_model_backend() -> ModelBackend:
    global _model_backend
    if _model_backend is None:
        backend_type = os.getenv("MODEL_BACKEND_TYPE", "mlx").lower()
        if backend_type == "mock":
            _model_backend = MockModelBackend()
        else:
            _model_backend = MLXModelBackend(dry_run_fallback=True)
    return _model_backend


def set_model_backend(backend: ModelBackend) -> None:
    global _model_backend
    _model_backend = backend


def get_sft_trainer() -> SFTTrainer:
    global _sft_trainer
    if _sft_trainer is None:
        _sft_trainer = SFTTrainer()
    return _sft_trainer


def set_sft_trainer(trainer: SFTTrainer) -> None:
    global _sft_trainer
    _sft_trainer = trainer


class LoadModelRequest(BaseModel):
    model_id: str = Field(description="Model identifier, e.g. Qwen/Qwen3-0.6B")
    revision: str = Field(default="main", description="Git commit SHA or tag")


class GenerateRequest(BaseModel):
    prompt: str = Field(description="Prompt text")
    seed: int = Field(default=42, description="Random seed")
    config: GenerationConfig = Field(default_factory=GenerationConfig)


class TrainSFTRequest(BaseModel):
    dataset_dir: str = Field(description="Directory containing train.jsonl")
    base_model: str = Field(default="Qwen/Qwen3-0.6B")
    revision: str = Field(default="main")
    config: SFTConfig = Field(default_factory=SFTConfig)
    seed: int = Field(default=42)
    training_run_id: str | None = Field(default=None)


class TrainRLRequest(BaseModel):
    base_model: str = Field(default="Qwen/Qwen3-0.6B")
    revision: str = Field(default="main")
    config: RLConfig = Field(default_factory=RLConfig)
    seed: int = Field(default=42)
    training_run_id: str | None = Field(default=None)


@app.get("/v1/health", response_model=HealthStatus)
def health_check() -> HealthStatus:
    backend = get_model_backend()
    return backend.health()


@app.get("/v1/capabilities", response_model=ModelCapabilities)
def get_capabilities() -> ModelCapabilities:
    backend = get_model_backend()
    return backend.capabilities()


@app.post("/v1/models/load")
def load_model(req: LoadModelRequest) -> dict[str, str]:
    backend = get_model_backend()
    try:
        backend.load(req.model_id, req.revision)
        return {
            "status": "loaded",
            "model_id": req.model_id,
            "revision": req.revision,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/v1/generate", response_model=GenerationResult)
def generate_code(req: GenerateRequest) -> GenerationResult:
    backend = get_model_backend()
    try:
        return backend.generate(req.prompt, req.seed, req.config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/v1/train/sft", response_model=SFTTrainingResult)
def train_sft(req: TrainSFTRequest) -> SFTTrainingResult:
    trainer = get_sft_trainer()
    try:
        return trainer.train(
            dataset_dir=req.dataset_dir,
            base_model=req.base_model,
            revision=req.revision,
            config=req.config,
            seed=req.seed,
            training_run_id=req.training_run_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/v1/train/rl", response_model=RLTrainingResult)
def train_rl(req: TrainRLRequest) -> RLTrainingResult:
    trainer = get_grpo_trainer()
    try:
        return trainer.train(
            base_model=req.base_model,
            revision=req.revision,
            config=req.config,
            seed=req.seed,
            training_run_id=req.training_run_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/v1/checkpoints", response_model=list[CheckpointManifest])
def list_checkpoints() -> list[CheckpointManifest]:
    trainer = get_sft_trainer()
    manifests: list[CheckpointManifest] = []
    for ckpt_dir in trainer.checkpoints_dir.iterdir():
        if ckpt_dir.is_dir() and (ckpt_dir / "manifest.json").exists():
            try:
                manifests.append(trainer.verify_checkpoint(ckpt_dir))
            except Exception:
                continue
    return manifests


@app.get("/v1/checkpoints/{checkpoint_id}", response_model=CheckpointManifest)
def get_checkpoint(checkpoint_id: str) -> CheckpointManifest:
    trainer = get_sft_trainer()
    ckpt_dir = trainer.checkpoints_dir / checkpoint_id
    if not ckpt_dir.exists():
        raise HTTPException(status_code=404, detail=f"Checkpoint not found: {checkpoint_id}")
    try:
        return trainer.verify_checkpoint(ckpt_dir)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Checkpoint verification failed: {e}") from e
