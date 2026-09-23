"""FastAPI control plane. Loopback by default; Tailscale IPv4 allowed at deploy (ADR 0034)."""

from __future__ import annotations

import socket
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from pydantic import BaseModel, Field

from .agent_loop import (
    cancel_agent_run,
    reconcile_stuck_running,
    resolve_pending_action,
    retry_agent_run,
    run_until_idle,
)
from .auth import auth_status, client_ip, require_auth
from .connect import connect_status, jupyter_open_url, read_token_file
from .conversation import AgentRun, AgentRunStatus, BillingClass, Conversation, Message, MessageRole
from .dispatch import DispatchFn, http_dispatch
from .model_router import CompletionRequest, ModelRouter, build_router_from_settings
from .policy import load_policy
from .secrets_store import PROVIDER_IDS, SecretStore, default_secret_store
from .settings import Settings
from .slice_graph import SliceState, build_slice_graph, thread_config
from .store import SqliteStore, WorkOrderStore
from .work_order import Status, WorkOrder

STATUS_HTML = Path(__file__).resolve().parent / "web" / "status.html"
AGENTS_HTML = Path(__file__).resolve().parent / "web" / "agents.html"
LAB_HTML = Path(__file__).resolve().parent / "web" / "lab.html"
SECRETS_HTML = Path(__file__).resolve().parent / "web" / "secrets.html"
HELP_HTML = Path(__file__).resolve().parent / "web" / "help.html"
WEB_DIR = Path(__file__).resolve().parent / "web"
STATIC_DIR = WEB_DIR / "static"
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
    reply: bool = Field(
        default=False,
        description="If true (user role), complete via model router and store assistant reply",
    )
    backend: str = Field(default="fake", description="Provider id when reply=true")
    model: str = Field(default="fake-instruct", description="Model id when reply=true")


class AgentRunIn(BaseModel):
    """Durable agent-run request. Distinct from an ordinary chat message."""

    objective: str = ""
    model: str = "fake-instruct"
    billing_class: str = Field(
        default="local",
        description="local|subscription_client|usage_billed_api (ADR 0038)",
    )
    backend: str = Field(default="fake", description="fake/scripted for tests; cloud disabled by default")
    work_order_id: str | None = Field(
        default=None,
        description="Optional runtime work-order UUID link; not an Implementation WO id",
    )
    execute: bool = Field(
        default=False,
        description="If true, run the bounded model/tool loop now (IWO-005)",
    )
    max_steps: int = Field(default=8, ge=1, le=64)


class ActionDecisionIn(BaseModel):
    decision: str = Field(description="approved|denied")
    action_id: str | None = None


class SecretValueIn(BaseModel):
    value: str = Field(min_length=1, max_length=8192)


class UsageBilledAuthIn(BaseModel):
    authorized: bool


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
    model_router: ModelRouter | None = None,
    secret_store: SecretStore | None = None,
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
    secrets = secret_store or default_secret_store()
    auth_mode = settings.auth_mode

    def _gate(request: Request, authorization: str | None = None) -> None:
        require_auth(
            mode=auth_mode,
            expected_token=token,
            authorization=authorization,
            request=request,
        )

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        yield
        if pg_context is not None:
            pg_context.__exit__(None, None, None)

    app = FastAPI(title="ai-lab control plane", version="0.5.0", lifespan=lifespan)
    app.state.store = store
    app.state.graph = graph
    app.state.checkpointer = checkpointer
    app.state.token = token
    app.state.settings = settings
    app.state.model_router = model_router or build_router_from_settings(settings, secret_store=secrets)
    app.state.secret_store = secrets
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

    @app.get("/agents", response_class=HTMLResponse)
    def agents_page() -> str:
        """Authenticated personal-agent UI shell (IWO-003). Token stays in the browser."""
        return AGENTS_HTML.read_text(encoding="utf-8")

    @app.get("/lab", response_class=HTMLResponse)
    def lab_page() -> str:
        """Connection hub — open Studio Jupyter without Air-side SSH tunnels (FEAT-012)."""
        return LAB_HTML.read_text(encoding="utf-8")

    @app.get("/secrets", response_class=HTMLResponse)
    def secrets_page() -> str:
        """Browser entry for foundation API keys (write-only; values never returned)."""
        return SECRETS_HTML.read_text(encoding="utf-8")

    @app.get("/help", response_class=HTMLResponse)
    def help_page() -> str:
        return HELP_HTML.read_text(encoding="utf-8")

    @app.get("/v1/auth/status")
    def auth_status_endpoint(request: Request) -> dict[str, object]:
        """Public: whether the browser must paste a bearer token."""
        return auth_status(
            mode=auth_mode,
            token_configured=bool(token),
            peer_ip=client_ip(request),
        )

    @app.get("/favicon.svg")
    def favicon() -> Response:
        return Response(content=FAVICON_SVG, media_type="image/svg+xml")

    @app.get("/v1/models")
    def list_models(request: Request, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        _gate(request, authorization)
        router: ModelRouter = app.state.model_router
        store_s: SecretStore = app.state.secret_store
        providers = router.list_providers()
        for p in providers:
            if p["id"] in PROVIDER_IDS:
                p["key_configured"] = store_s.has_provider(p["id"])
        return {
            "providers": providers,
            "usage_billed_authorized": store_s.usage_billed_authorized(),
            "note": "Cloud complete() stays blocked until usage_billed_authorized (ADR 0038).",
        }

    @app.get("/v1/secrets/status")
    def secrets_status(request: Request, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        _gate(request, authorization)
        store_s: SecretStore = app.state.secret_store
        return store_s.status()

    @app.put("/v1/secrets/providers/{provider_id}")
    def put_provider_secret(
        request: Request,
        provider_id: str,
        body: SecretValueIn,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _gate(request, authorization)
        store_s: SecretStore = app.state.secret_store
        try:
            store_s.set_provider(provider_id, body.value)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"ok": True, "id": provider_id, "configured": True}

    @app.delete("/v1/secrets/providers/{provider_id}")
    def delete_provider_secret(
        request: Request,
        provider_id: str,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _gate(request, authorization)
        store_s: SecretStore = app.state.secret_store
        try:
            cleared = store_s.clear_provider(provider_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"ok": True, "id": provider_id, "configured": False, "cleared": cleared}

    @app.put("/v1/secrets/usage-billed")
    def put_usage_billed(
        request: Request,
        body: UsageBilledAuthIn,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _gate(request, authorization)
        store_s: SecretStore = app.state.secret_store
        store_s.set_usage_billed_authorized(body.authorized)
        return {
            "ok": True,
            "usage_billed_authorized": store_s.usage_billed_authorized(),
            "note": "Authorization flag only; live HTTP adapters are a follow-on IWO.",
        }

    @app.get("/v1/connect/status")
    def connect_status_endpoint() -> dict[str, Any]:
        """Studio reachability from the mini. Never includes secret values."""
        jtoken = read_token_file(settings.studio_jupyter_token_file)
        return connect_status(
            jupyter_url=settings.studio_jupyter_url,
            ollama_url=settings.studio_ollama_url,
            jupyter_token=jtoken,
            studio_worker_url=settings.studio_worker_url,
        )

    @app.get("/v1/connect/jupyter")
    def connect_jupyter(request: Request, authorization: str | None = Header(default=None)) -> dict[str, str]:
        """Return a one-shot Studio Jupyter open URL. Requires lab API token."""
        _gate(request, authorization)
        if not settings.studio_jupyter_url:
            raise HTTPException(
                status_code=503,
                detail="STUDIO_JUPYTER_URL not configured on the mini",
            )
        jtoken = read_token_file(settings.studio_jupyter_token_file)
        if not jtoken:
            raise HTTPException(
                status_code=503,
                detail="Studio Jupyter token file missing on the mini",
            )
        return {
            "open_url": jupyter_open_url(settings.studio_jupyter_url, jtoken),
            "note": "Open in a new tab on the tailnet. Do not commit this URL.",
        }

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
        request: Request,
        body: WorkOrderIn,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _gate(request, authorization)
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
    def get_work_order(request: Request, order_id: str, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        _gate(request, authorization)
        order = store.get(order_id)
        if order is None:
            raise HTTPException(status_code=404, detail="not found")
        snapshot = graph.get_state(thread_config(order_id))
        data = order.to_dict()
        data["graph_next"] = list(snapshot.next)
        return data

    @app.post("/v1/work-orders/{order_id}/approve")
    def approve_work_order(
        request: Request,
        order_id: str,
        body: ApproveIn,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _gate(request, authorization)
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
        request: Request,
        body: ConversationIn,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _gate(request, authorization)
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
        request: Request,
        conversation_id: str,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _gate(request, authorization)
        conversation = store.get_conversation(conversation_id)  # type: ignore[attr-defined]
        if conversation is None:
            raise HTTPException(status_code=404, detail="not found")
        return conversation.to_dict()

    @app.post("/v1/conversations/{conversation_id}/messages")
    def post_message(
        request: Request,
        conversation_id: str,
        body: MessageIn,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        """Persist an ordinary chat turn. Optionally complete a model reply (not an agent run)."""
        _gate(request, authorization)
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

        if not body.reply or role != MessageRole.USER:
            return message.to_dict()

        from .cloud_backends import CloudUnavailable
        from .ollama_backend import OllamaUnavailable

        prior = store.list_messages(conversation_id)  # type: ignore[attr-defined]
        # Build a short transcript prompt (exclude the just-stored user turn duplicate at end).
        lines: list[str] = []
        for m in prior[-12:]:
            lines.append(f"{m.role.value}: {m.content}")
        prompt = "\n".join(lines) if lines else body.content
        router: ModelRouter = app.state.model_router
        try:
            completion = router.complete(
                CompletionRequest(
                    model=body.model,
                    prompt=prompt,
                    backend=body.backend,
                    system=f"You are the {conversation.agent} agent in ai-lab. Reply helpfully and briefly.",
                )
            )
        except (PermissionError, KeyError, OllamaUnavailable, CloudUnavailable) as exc:
            return {
                "message": message.to_dict(),
                "reply": None,
                "error": f"provider_unavailable:{exc}",
            }
        assistant = Message.new(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=completion.text,
            meta={
                "kind": "chat_reply",
                "backend": completion.backend,
                "model": completion.model,
                "billing_class": completion.billing_class.value,
            },
        )
        store.put_message(assistant)  # type: ignore[attr-defined]
        return {
            "message": message.to_dict(),
            "reply": assistant.to_dict(),
            "error": None,
        }

    @app.get("/v1/conversations/{conversation_id}/messages")
    def list_messages(
        request: Request,
        conversation_id: str,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _gate(request, authorization)
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
        request: Request,
        conversation_id: str,
        body: AgentRunIn,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        """Create a durable agent run. Optionally execute the bounded loop."""
        _gate(request, authorization)
        conversation = store.get_conversation(conversation_id)  # type: ignore[attr-defined]
        if conversation is None:
            raise HTTPException(status_code=404, detail="not found")
        try:
            billing = BillingClass(body.billing_class)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"invalid billing_class: {body.billing_class}") from exc
        if billing == BillingClass.USAGE_BILLED_API and body.backend not in {"fake", "scripted"}:
            secrets_s: SecretStore = app.state.secret_store
            if not secrets_s.usage_billed_authorized():
                raise HTTPException(
                    status_code=400,
                    detail="usage_billed_api disabled until authorized on /secrets (ADR 0038)",
                )
            if body.backend in PROVIDER_IDS and not secrets_s.has_provider(body.backend):
                raise HTTPException(
                    status_code=400,
                    detail=f"{body.backend} API key not configured on /secrets",
                )
        from .conversation import RunBudget

        run = AgentRun.new(
            agent=conversation.agent,
            objective=body.objective,
            conversation_id=conversation_id,
            work_order_id=body.work_order_id,
            model=body.model,
            billing_class=billing,
            backend=body.backend,
            budget=RunBudget(max_steps=body.max_steps),
        )
        router: ModelRouter = app.state.model_router
        if body.execute:
            run.status = AgentRunStatus.QUEUED
            store.put_agent_run(run)  # type: ignore[attr-defined]
            run = run_until_idle(
                run,
                router=router,
                store_put=store.put_agent_run,  # type: ignore[attr-defined]
            )
        else:
            run.status = AgentRunStatus.CREATED
            store.put_agent_run(run)  # type: ignore[attr-defined]
        out = run.to_dict()
        out["kind"] = "agent_run"
        out["note"] = (
            "Durable agent run. Distinct from chat messages and from "
            "POST /v1/work-orders. Set execute=true to run the mini model/tool loop."
        )
        return out

    @app.get("/v1/agent-runs/{run_id}")
    def get_agent_run(
        request: Request,
        run_id: str,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _gate(request, authorization)
        run = store.get_agent_run(run_id)  # type: ignore[attr-defined]
        if run is None:
            raise HTTPException(status_code=404, detail="not found")
        out = run.to_dict()
        out["kind"] = "agent_run"
        return out

    @app.post("/v1/agent-runs/{run_id}/tick")
    def tick_agent_run(
        request: Request,
        run_id: str,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _gate(request, authorization)
        run = store.get_agent_run(run_id)  # type: ignore[attr-defined]
        if run is None:
            raise HTTPException(status_code=404, detail="not found")
        run = run_until_idle(
            run,
            router=app.state.model_router,
            store_put=store.put_agent_run,  # type: ignore[attr-defined]
        )
        out = run.to_dict()
        out["kind"] = "agent_run"
        return out

    @app.post("/v1/agent-runs/{run_id}/cancel")
    def cancel_run(
        request: Request,
        run_id: str,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _gate(request, authorization)
        run = store.get_agent_run(run_id)  # type: ignore[attr-defined]
        if run is None:
            raise HTTPException(status_code=404, detail="not found")
        run = cancel_agent_run(run, store.put_agent_run)  # type: ignore[attr-defined]
        return run.to_dict()

    @app.post("/v1/agent-runs/{run_id}/retry")
    def retry_run(
        request: Request,
        run_id: str,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _gate(request, authorization)
        run = store.get_agent_run(run_id)  # type: ignore[attr-defined]
        if run is None:
            raise HTTPException(status_code=404, detail="not found")
        try:
            run = retry_agent_run(run, store.put_agent_run)  # type: ignore[attr-defined]
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        run = run_until_idle(
            run,
            router=app.state.model_router,
            store_put=store.put_agent_run,  # type: ignore[attr-defined]
        )
        return run.to_dict()

    @app.post("/v1/agent-runs/{run_id}/reconcile")
    def reconcile_run(
        request: Request,
        run_id: str,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _gate(request, authorization)
        run = store.get_agent_run(run_id)  # type: ignore[attr-defined]
        if run is None:
            raise HTTPException(status_code=404, detail="not found")
        run = reconcile_stuck_running(run, store.put_agent_run)  # type: ignore[attr-defined]
        return run.to_dict()

    @app.post("/v1/agent-runs/{run_id}/approve-action")
    def approve_action(
        request: Request,
        run_id: str,
        body: ActionDecisionIn,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        """Approve or deny one pending tool action (IWO-007). Not an IWO/plan approval."""
        _gate(request, authorization)
        run = store.get_agent_run(run_id)  # type: ignore[attr-defined]
        if run is None:
            raise HTTPException(status_code=404, detail="not found")
        if run.pending_action and body.action_id and body.action_id != run.pending_action.get("id"):
            raise HTTPException(status_code=400, detail="action_id mismatch")
        run = resolve_pending_action(
            run,
            decision=body.decision,
            router=app.state.model_router,
            store_put=store.put_agent_run,  # type: ignore[attr-defined]
        )
        out = run.to_dict()
        out["kind"] = "agent_run"
        out["note"] = "Action-level decision; distinct from Implementation WO plan approval."
        return out

    @app.get("/v1/conversations/{conversation_id}/runs")
    def list_conversation_runs(
        request: Request,
        conversation_id: str,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _gate(request, authorization)
        conversation = store.get_conversation(conversation_id)  # type: ignore[attr-defined]
        if conversation is None:
            raise HTTPException(status_code=404, detail="not found")
        runs = store.list_agent_runs(conversation_id)  # type: ignore[attr-defined]
        return {
            "conversation_id": conversation_id,
            "runs": [r.to_dict() for r in runs],
        }

    if STATIC_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    return app


def app_factory() -> FastAPI:
    """Uvicorn factory. Avoids connecting to Postgres at import time."""
    return create_control_app()
