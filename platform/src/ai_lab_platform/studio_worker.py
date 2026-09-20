"""Studio worker HTTP surface. Runs on the compute plane, not the M1.

Executes the same deterministic local plans as the laptop worker. Not an LLM.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .agent_plans import execute_plan
from .policy import constrain_tools, load_policy
from .tools import ToolContext


class TaskIn(BaseModel):
    work_order_id: str
    objective: str
    agent: str = ""
    bounded_scope: str = ""
    allowed_tools: list[str] = Field(default_factory=list)
    approved_tools: list[str] = Field(default_factory=list)


class TaskOut(BaseModel):
    ok: bool = True
    work_order_id: str
    detail: str = Field(description="Deterministic plan output; not an LLM completion")
    artifacts: list[str] = Field(default_factory=list)
    tools_run: list[str] = Field(default_factory=list)
    blocked_tool: str | None = None


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def default_workspace_root() -> Path:
    raw = os.environ.get("AI_LAB_WORKSPACE", "").strip()
    return Path(raw).expanduser() if raw else _repo_root()


def default_artifact_root() -> Path:
    raw = os.environ.get("AI_LAB_ARTIFACT_ROOT", "").strip()
    if raw:
        return Path(raw).expanduser()
    return Path.home() / ".ai-lab" / "artifacts"


def create_worker_app(
    *,
    workspace_root: Path | None = None,
    artifact_root: Path | None = None,
    agents_root: Path | None = None,
) -> FastAPI:
    workspace_root = workspace_root or default_workspace_root()
    artifact_root = artifact_root or default_artifact_root()
    app = FastAPI(title="ai-lab studio worker", version="0.2.0")
    app.state.workspace_root = workspace_root
    app.state.artifact_root = artifact_root

    @app.get("/health")
    def health() -> dict[str, object]:
        return {
            "ok": True,
            "role": "studio-worker",
            "plans": "deterministic-local",
            "llm": False,
            "deployed": False,
        }

    @app.post("/v1/tasks", response_model=TaskOut)
    def run_task(task: TaskIn) -> TaskOut:
        try:
            policy = load_policy(task.agent, agents_root=agents_root)
        except (OSError, ValueError) as exc:
            return TaskOut(
                ok=False,
                work_order_id=task.work_order_id,
                detail=f"unknown agent policy: {exc}",
            )
        requested = task.allowed_tools or list(policy.allowed_tools)
        allowed = constrain_tools(requested, policy)
        ctx = ToolContext(
            workspace_root=workspace_root,
            artifact_root=artifact_root / task.work_order_id,
            bounded_scope=task.bounded_scope,
        )
        result = execute_plan(
            task.agent,
            task.objective,
            ctx,
            allowed,
            set(task.approved_tools),
        )
        return TaskOut(
            ok=result.ok,
            work_order_id=task.work_order_id,
            detail=result.detail,
            artifacts=result.artifacts,
            tools_run=result.tools_run,
            blocked_tool=result.blocked_tool,
        )

    return app


def app_factory() -> FastAPI:
    return create_worker_app()
