"""FastAPI control plane. Binds loopback by default. Not deployed on the M1 yet."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from pydantic import BaseModel, Field

from .dispatch import DispatchFn, http_dispatch
from .policy import load_policy
from .settings import Settings
from .slice_graph import SliceState, build_slice_graph, thread_config
from .store import SqliteStore, WorkOrderStore
from .work_order import Status, WorkOrder


def default_sqlite_path() -> Path:
    path = Path.home() / ".ai-lab" / "harness.sqlite"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


class WorkOrderIn(BaseModel):
    agent: str
    objective: str
    bounded_scope: str = ""


class ApproveIn(BaseModel):
    decision: str = Field(default="approved", description="approved|rejected")


def _auth(expected: str, authorization: str | None) -> None:
    if not expected:
        return
    if authorization != f"Bearer {expected}":
        raise HTTPException(status_code=401, detail="unauthorized")


def _postgres_checkpointer(database_url: str) -> tuple[Any, Any]:
    from langgraph.checkpoint.postgres import PostgresSaver

    context = PostgresSaver.from_conn_string(database_url)
    saver = context.__enter__()
    saver.setup()
    return saver, context


def create_control_app(
    *,
    store: WorkOrderStore | None = None,
    dispatch: DispatchFn | None = None,
    checkpointer: Any | None = None,
    token: str = "",
    studio_worker_url: str | None = None,
    settings: Settings | None = None,
) -> FastAPI:
    settings = settings or Settings.from_env()
    token = token or settings.api_token
    studio_worker_url = studio_worker_url or settings.studio_worker_url
    pg_context: Any = None

    if store is None:
        if settings.database_url:
            from .postgres_store import PostgresStore

            store = PostgresStore(settings.database_url)
        else:
            store = SqliteStore(default_sqlite_path())

    if checkpointer is None:
        if settings.database_url:
            checkpointer, pg_context = _postgres_checkpointer(settings.database_url)
        else:
            checkpointer = MemorySaver()

    dispatch = dispatch or http_dispatch(studio_worker_url)
    graph = build_slice_graph(store, dispatch, checkpointer)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        yield
        if pg_context is not None:
            pg_context.__exit__(None, None, None)

    app = FastAPI(title="ai-lab control plane", version="0.3.0", lifespan=lifespan)
    app.state.store = store
    app.state.graph = graph
    app.state.checkpointer = checkpointer
    app.state.token = token
    app.state.settings = settings
    checkpoint_backend = "postgres" if settings.database_url else "memory"

    @app.get("/health")
    def health() -> dict[str, object]:
        return {
            "ok": True,
            "role": "control-plane",
            "orchestrator": "langgraph",
            "work_order_store": type(store).__name__,
            "checkpoints": checkpoint_backend,
            "deployed": False,
        }

    @app.post("/v1/work-orders")
    def submit_work_order(
        body: WorkOrderIn,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _auth(token, authorization)
        try:
            policy = load_policy(body.agent)
        except (OSError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        order = WorkOrder.new(
            objective=body.objective,
            agent=body.agent,
            allowed_tools=list(policy.allowed_tools),
            bounded_scope=body.bounded_scope,
        )
        store.put(order)
        store.set_status(order.id, Status.QUEUED)
        payload: SliceState = {
            "work_order_id": order.id,
            "objective": order.objective,
            "agent": order.agent,
            "studio_ok": False,
            "studio_detail": "",
            "error": "",
            "approval": "",
        }
        result = graph.invoke(payload, thread_config(order.id))
        current = store.get(order.id)
        out = current.to_dict() if current else order.to_dict()
        out["interrupted"] = bool(result.get("__interrupt__"))
        out["graph_error"] = result.get("error") or ""
        return out

    @app.get("/v1/work-orders/{order_id}")
    def get_work_order(order_id: str, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        _auth(token, authorization)
        order = store.get(order_id)
        if order is None:
            raise HTTPException(status_code=404, detail="not found")
        snapshot = graph.get_state(thread_config(order_id))
        data = order.to_dict()
        data["graph_next"] = list(snapshot.next)
        return data

    @app.post("/v1/work-orders/{order_id}/approve")
    def approve_work_order(
        order_id: str,
        body: ApproveIn,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _auth(token, authorization)
        order = store.get(order_id)
        if order is None:
            raise HTTPException(status_code=404, detail="not found")
        graph.invoke(Command(resume=body.decision), thread_config(order_id))
        current = store.get(order_id)
        if current is None:
            raise HTTPException(status_code=404, detail="not found")
        return current.to_dict()

    return app


def app_factory() -> FastAPI:
    """Uvicorn factory. Avoids connecting to Postgres at import time."""
    return create_control_app()
