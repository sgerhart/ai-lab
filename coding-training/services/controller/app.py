from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any, AsyncGenerator

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from packages.contracts import (
    GenerationConfig,
    HealthStatus,
    SandboxPolicy,
)
from packages.datasets.task_loader import TaskLoader
from services.model.backend import MockModelBackend, ModelBackend
from services.rewards.engine import RewardEngine
from services.sandbox_worker.backend import MockSandboxBackend, SandboxBackend
from .loop import ExecutionLoopOrchestrator
from .store import JobStore

app = FastAPI(
    title="AI Lab Coding Model Training Controller",
    version="1.0.0",
    description="Control plane orchestrating model code generation, sandbox execution, and reward scoring",
)

# Global controller state and singletons
store = JobStore()
reward_engine = RewardEngine()
orchestrator = ExecutionLoopOrchestrator(store=store, reward_engine=reward_engine)

# Active backends (defaults to mock backends for zero-privilege/dry-run safety)
active_model_backend: ModelBackend = MockModelBackend()
active_sandbox_backend: SandboxBackend = MockSandboxBackend()


class JobSubmitRequest(BaseModel):
    """Payload to trigger an execution loop for a task."""
    task_id: str
    prompt: str
    test_bundle_ref: str
    test_bundle_sha256: str = Field(min_length=64, max_length=64)
    family_id: str = "generic"
    generation_config: GenerationConfig = Field(default_factory=GenerationConfig)
    sandbox_policy: SandboxPolicy = Field(default_factory=SandboxPolicy)


@app.get("/v1/health", response_model=HealthStatus)
def get_health() -> HealthStatus:
    """Returns controller service health and backend reachability."""
    model_h = active_model_backend.health()
    sandbox_h = active_sandbox_backend.health()
    all_healthy = model_h.healthy and sandbox_h.healthy

    return HealthStatus(
        healthy=all_healthy,
        status="ok" if all_healthy else "degraded",
        details={
            "controller": "online",
            "model_worker": model_h.status,
            "sandbox_worker": sandbox_h.status,
        },
    )


@app.get("/v1/metrics")
def get_metrics() -> dict[str, Any]:
    """Returns global platform execution metrics and reward statistics."""
    return store.get_summary_metrics()


@app.get("/v1/jobs")
def list_jobs(
    limit: int = Query(default=50, ge=1, le=500),
    state: str | None = Query(default=None),
) -> list[dict[str, Any]]:
    """Lists jobs with optional status filter."""
    return store.list_jobs(limit=limit, state=state)


@app.get("/v1/jobs/{job_id}")
def get_job(job_id: str) -> dict[str, Any]:
    """Fetches comprehensive job details including execution and reward."""
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return job


@app.post("/v1/jobs/submit")
def submit_job(req: JobSubmitRequest) -> dict[str, Any]:
    """Submits a programming task to the generation and execution pipeline."""
    from packages.contracts import Split, Task

    task_obj = Task(
        task_id=req.task_id,
        prompt=req.prompt,
        function_contract=f"def {req.task_id}(*args) -> Any:",
        source_provenance="controller_api_submit",
        test_bundle_ref=req.test_bundle_ref,
        test_bundle_sha256=req.test_bundle_sha256,
        split=Split.TRAIN,
        difficulty="medium",
        family_id=req.family_id,
    )

    result = orchestrator.run_task(
        task=task_obj,
        model=active_model_backend,
        sandbox=active_sandbox_backend,
        gen_config=req.generation_config,
        sandbox_policy=req.sandbox_policy,
        actor="controller_api",
    )

    return {
        "job_id": result.job_id,
        "task_id": result.task_id,
        "candidate_sha256": result.candidate_sha256,
        "status": result.execution.status.value,
        "reward": result.reward.reward,
        "is_scorable": result.reward.is_scorable,
        "failure_class": result.execution.failure_class.value,
        "elapsed_ms": result.execution.elapsed_ms,
    }


@app.get("/v1/audit/events")
def list_audit_events(limit: int = Query(default=50, ge=1, le=500)) -> list[dict[str, Any]]:
    """Returns immutable security and execution audit events."""
    return store.list_audit_events(limit=limit)


@app.get("/v1/events/stream")
async def event_stream() -> StreamingResponse:
    """Server-Sent Events (SSE) telemetry stream for real-time console observer (WO-10)."""
    async def sse_generator() -> AsyncGenerator[str, None]:
        for _ in range(5):
            metrics = store.get_summary_metrics()
            payload = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metrics": metrics,
            }
            yield f"data: {json.dumps(payload)}\n\n"
            await asyncio.sleep(1.0)

    return StreamingResponse(sse_generator(), media_type="text/event-stream")


@app.get("/v1/tasks")
def list_tasks(
    split: str | None = Query(default=None),
    difficulty: str | None = Query(default=None),
) -> list[dict[str, Any]]:
    """Lists curated programming tasks with optional split and difficulty filters."""
    loader = TaskLoader()
    tasks = loader.load_tasks()

    if split:
        tasks = [t for t in tasks if t.split.value == split.lower()]
    if difficulty:
        tasks = [t for t in tasks if t.difficulty.lower() == difficulty.lower()]

    return [
        {
            "task_id": t.task_id,
            "prompt": t.prompt,
            "entry_point": (
                t.function_contract.split("(")[0].replace("def ", "").strip()
                if "(" in t.function_contract
                else t.task_id
            ),
            "function_contract": t.function_contract,
            "difficulty": t.difficulty,
            "split": t.split.value,
            "family_id": t.family_id,
            "assertion_count": 20,
            "test_bundle_sha256": t.test_bundle_sha256,
        }
        for t in tasks
    ]



@app.get("/v1/models")
def list_models() -> dict[str, Any]:
    """Returns catalog of base models and verified on-disk checkpoints."""
    checkpoints_dir = Path(os.getenv("AI_LAB_CHECKPOINTS_DIR", str(Path.home() / ".ai-lab" / "models" / "adapters")))
    checkpoints = []
    if checkpoints_dir.exists():
        for ckpt in checkpoints_dir.iterdir():
            if ckpt.is_dir() and (ckpt / "manifest.json").exists():
                try:
                    data = json.loads((ckpt / "manifest.json").read_text(encoding="utf-8"))
                    checkpoints.append(data)
                except Exception:
                    continue

    return {
        "base_models": [
            {
                "model_id": "Qwen/Qwen3-0.6B",
                "parameters": "0.6B",
                "framework": "mlx-lm",
                "device": "mac-studio (M5 Max)",
                "status": "ready",
            },
            {
                "model_id": "deepseek-ai/DeepSeek-Coder-1.3B",
                "parameters": "1.3B",
                "framework": "mlx-lm",
                "device": "mac-studio (M5 Max)",
                "status": "cataloged",
            },
        ],
        "checkpoints": checkpoints,
    }


# Mount compiled web console if present
console_dist = Path(__file__).resolve().parents[2] / "console" / "dist"
if console_dist.exists():
    app.mount("/console", StaticFiles(directory=str(console_dist), html=True), name="console")

    @app.get("/")
    def root_redirect() -> RedirectResponse:
        return RedirectResponse(url="/console/")
