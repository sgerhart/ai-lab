"""FastAPI control plane. Loopback by default; Tailscale IPv4 allowed at deploy (ADR 0034)."""

from __future__ import annotations

import socket
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse, Response
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from pydantic import BaseModel, Field

from .conversation import AgentRun, AgentRunStatus, BillingClass, Conversation, Message, MessageRole
from .dispatch import DispatchFn, http_dispatch
from .model_router import CompletionRequest, FakeBackend, ModelRouter
from .policy import load_policy
from .settings import Settings
from .slice_graph import SliceState, build_slice_graph, thread_config
from .store import SqliteStore, WorkOrderStore
from .work_order import Status, WorkOrder

STATUS_HTML = Path(__file__).resolve().parent / "web" / "status.html"
FAVICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="6" fill="#141b22"/>
  <circle cx="16" cy="16" r="6" fill="#3ee0a8"/>
</svg>
"""


def _port_open(host: str, port: int, timeout: float = 0.2) -> bool:
    sock = socket.socket()
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def _http_ok(url: str, timeout: float = 0.4) -> bool:
    try:
        with urlopen(url, timeout=timeout) as resp:  # noqa: S310 — operator-set loopback worker
            return 200 <= getattr(resp, "status", 0) < 300
    except (URLError, OSError, ValueError):
        return False


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


class ConversationIn(BaseModel):
    agent: str
    title: str = ""


class MessageIn(BaseModel):
    """Ordinary chat turn. Does not create a runtime work order or agent run."""

    content: str
    role: str = Field(default="user", description="user|assistant|system|tool")


class AgentRunIn(BaseModel):
    """Durable agent-run request. Distinct from an ordinary chat message.

    Does not start the full model/tool loop (IWO-005). With backend=fake,
    records a FakeBackend placeholder trace for contract tests.
    """

    objective: str = ""
    model: str = "fake-instruct"
    billing_class: str = Field(
        default="local",
        description="local|subscription_client|usage_billed_api (ADR 0038)",
    )
    backend: str = Field(default="fake", description="fake for tests; cloud disabled by default")
    work_order_id: str | None = Field(
        default=None,
        description="Optional runtime work-order UUID link; not an Implementation WO id",
    )

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

    app = FastAPI(title="ai-lab control plane", version="0.4.0", lifespan=lifespan)
    app.state.store = store
    app.state.graph = graph
    app.state.checkpointer = checkpointer
    app.state.token = token
    app.state.settings = settings
    app.state.model_router = ModelRouter(backends={"fake": FakeBackend(), "ollama": FakeBackend()})
    checkpoint_backend = "postgres" if settings.database_url else "memory"

    @app.get("/health")
    def health() -> dict[str, object]:
        return {
            "ok": True,
            "role": "control-plane",
            "orchestrator": "langgraph",
            "work_order_store": type(store).__name__,
            "checkpoints": checkpoint_backend,
            "deployed": bool(settings.database_url),
        }

    @app.get("/", response_class=HTMLResponse)
    def status_page() -> str:
        return STATUS_HTML.read_text(encoding="utf-8")

    @app.get("/favicon.svg")
    def favicon() -> Response:
        return Response(content=FAVICON_SVG, media_type="image/svg+xml")

    @app.get("/v1/status")
    def lab_status() -> dict[str, object]:
        studio_url = (settings.studio_worker_url or "http://127.0.0.1:8090").rstrip("/")
        studio_open = _port_open("127.0.0.1", 8090)
        counts = {item.value: 0 for item in Status}
        try:
            for order in store.list():
                counts[order.status.value] = counts.get(order.status.value, 0) + 1
        except Exception:
            counts = {}
        return {
            "ok": True,
            "role": "control-plane",
            "host": "mac-mini",
            "orchestrator": "langgraph",
            "work_order_store": type(store).__name__,
            "checkpoints": checkpoint_backend,
            "deployed": bool(settings.database_url),
            "services": {
                "postgres": {"port": 5432, "open": _port_open("127.0.0.1", 5432)},
                "redis": {"port": 6379, "open": _port_open("127.0.0.1", 6379)},
                "qdrant": {"port": 6333, "open": _port_open("127.0.0.1", 6333)},
                "studio": {
                    "port": 8090,
                    "open": studio_open,
                    "health": _http_ok(f"{studio_url}/health") if studio_open else False,
                },
            },
            "work_orders": counts,
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

    # --- Conversations / agent runs (FEAT-010 / IWO-002) -------------------
    # Chat messages ≠ durable agent runs ≠ runtime work orders ≠ Implementation WOs.

    @app.post("/v1/conversations")
    def create_conversation(
        body: ConversationIn,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _auth(token, authorization)
        try:
            load_policy(body.agent)
        except (OSError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if not hasattr(store, "put_conversation"):
            raise HTTPException(status_code=501, detail="conversation store unavailable")
        conversation = Conversation.new(agent=body.agent, title=body.title)
        store.put_conversation(conversation)  # type: ignore[attr-defined]
        return conversation.to_dict()

    @app.get("/v1/conversations/{conversation_id}")
    def get_conversation(
        conversation_id: str,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _auth(token, authorization)
        conversation = store.get_conversation(conversation_id)  # type: ignore[attr-defined]
        if conversation is None:
            raise HTTPException(status_code=404, detail="not found")
        return conversation.to_dict()

    @app.post("/v1/conversations/{conversation_id}/messages")
    def post_message(
        conversation_id: str,
        body: MessageIn,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        """Persist an ordinary chat turn. Does not enqueue a work order or agent run."""
        _auth(token, authorization)
        conversation = store.get_conversation(conversation_id)  # type: ignore[attr-defined]
        if conversation is None:
            raise HTTPException(status_code=404, detail="not found")
        try:
            role = MessageRole(body.role)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"invalid role: {body.role}") from exc
        message = Message.new(
            conversation_id=conversation_id,
            role=role,
            content=body.content,
            meta={"kind": "chat_turn"},
        )
        store.put_message(message)  # type: ignore[attr-defined]
        return message.to_dict()

    @app.get("/v1/conversations/{conversation_id}/messages")
    def list_messages(
        conversation_id: str,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _auth(token, authorization)
        conversation = store.get_conversation(conversation_id)  # type: ignore[attr-defined]
        if conversation is None:
            raise HTTPException(status_code=404, detail="not found")
        messages = store.list_messages(conversation_id)  # type: ignore[attr-defined]
        return {
            "conversation_id": conversation_id,
            "messages": [m.to_dict() for m in messages],
            "note": "Ordinary chat turns only; not runtime work orders.",
        }

    @app.post("/v1/conversations/{conversation_id}/runs")
    def create_agent_run(
        conversation_id: str,
        body: AgentRunIn,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        """Create a durable agent run. Not an ordinary chat message.

        FakeBackend may write a placeholder trace. Full model/tool loop is IWO-005.
        """
        _auth(token, authorization)
        conversation = store.get_conversation(conversation_id)  # type: ignore[attr-defined]
        if conversation is None:
            raise HTTPException(status_code=404, detail="not found")
        try:
            billing = BillingClass(body.billing_class)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"invalid billing_class: {body.billing_class}") from exc
        if billing == BillingClass.USAGE_BILLED_API and body.backend not in {"fake"}:
            raise HTTPException(
                status_code=400,
                detail="usage_billed_api providers are disabled until owner enables credentials",
            )
        run = AgentRun.new(
            agent=conversation.agent,
            objective=body.objective,
            conversation_id=conversation_id,
            work_order_id=body.work_order_id,
            model=body.model,
            billing_class=billing,
            backend=body.backend,
        )
        if body.backend == "fake":
            router: ModelRouter = app.state.model_router
            completion = router.complete(
                CompletionRequest(model=body.model, prompt=body.objective or "(no objective)", backend="fake")
            )
            run.traces.append(
                {
                    "kind": "placeholder_model_call",
                    "note": "Not the FEAT-010 model/tool loop; FakeBackend contract only (IWO-002).",
                    "billing_class": billing.value,
                    "response": completion.text,
                }
            )
        run.status = AgentRunStatus.CREATED
        store.put_agent_run(run)  # type: ignore[attr-defined]
        out = run.to_dict()
        out["kind"] = "agent_run"
        out["note"] = (
            "Durable agent run record. Distinct from chat messages and from "
            "POST /v1/work-orders runtime jobs. Model/tool loop: IWO-005."
        )
        return out

    @app.get("/v1/agent-runs/{run_id}")
    def get_agent_run(
        run_id: str,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _auth(token, authorization)
        run = store.get_agent_run(run_id)  # type: ignore[attr-defined]
        if run is None:
            raise HTTPException(status_code=404, detail="not found")
        out = run.to_dict()
        out["kind"] = "agent_run"
        return out

    @app.get("/v1/conversations/{conversation_id}/runs")
    def list_conversation_runs(
        conversation_id: str,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _auth(token, authorization)
        conversation = store.get_conversation(conversation_id)  # type: ignore[attr-defined]
        if conversation is None:
            raise HTTPException(status_code=404, detail="not found")
        runs = store.list_agent_runs(conversation_id)  # type: ignore[attr-defined]
        return {
            "conversation_id": conversation_id,
            "runs": [r.to_dict() for r in runs],
        }

    return app


def app_factory() -> FastAPI:
    """Uvicorn factory. Avoids connecting to Postgres at import time."""
    return create_control_app()
