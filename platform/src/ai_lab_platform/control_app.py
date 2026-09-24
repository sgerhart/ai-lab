"""FastAPI control plane. Loopback by default; Tailscale IPv4 allowed at deploy (ADR 0034)."""

from __future__ import annotations

import json
import socket
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

from fastapi import FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from pydantic import BaseModel, Field

from .agent_definitions import AgentDefinition, default_agent_definition_store
from .agent_loop import (
    cancel_agent_run,
    reconcile_stuck_running,
    resolve_pending_action,
    retry_agent_run,
    run_until_idle,
)
from .agent_scheduler import status as scheduler_status
from .agent_scheduler import tick as scheduler_tick
from .agent_worker import AgentRunWorker, drain_queued_runs
from .attachments import AttachmentError, default_attachment_store
from .auth import AuthError, auth_status, client_ip, require_auth
from .operator_auth import login as operator_login
from .operator_auth import revoke_session
from .connect import connect_status, jupyter_open_url, read_token_file
from .conversation import AgentRun, AgentRunStatus, BillingClass, Conversation, Message, MessageRole
from .dispatch import DispatchFn, http_dispatch
from .mcp_client import (
    McpDenied,
    McpTransportError,
    delete_local_server,
    list_mcp_tools,
    mcp_client_status,
    require_mcp_servers,
    upsert_local_server,
)
from .model_router import CompletionRequest, ModelRouter, build_router_from_settings
from .policy import load_policy
from .schedule_cron import CronError, parse_cron
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
    attachment_ids: list[str] = Field(default_factory=list)
    deep_research: bool = Field(
        default=False,
        description="If true, prefer usage-billed frontier backend when authorized (IWO-028)",
    )


class AgentDefinitionIn(BaseModel):
    title: str
    agent: str = "lab-operations"
    system_prompt: str = ""
    tools: list[str] = Field(default_factory=list)
    mcp_server_ids: list[str] = Field(default_factory=list)
    schedule_cron: str = ""


class AgentDefinitionRunIn(BaseModel):
    objective: str = ""
    model: str = "llama3.2:3b"
    backend: str = "ollama"
    billing_class: str = "local"
    max_steps: int = Field(default=8, ge=1, le=64)
    conversation_id: str | None = None


class McpServerIn(BaseModel):
    id: str
    label: str = ""
    transport: str = "stdio"
    command: str = ""
    args: list[str] = Field(default_factory=list)
    enabled: bool = True


class LoginIn(BaseModel):
    username: str
    password: str


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
        try:
            require_auth(
                mode=auth_mode,
                expected_token=token,
                authorization=authorization,
                request=request,
            )
        except AuthError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        worker: AgentRunWorker | None = None
        if settings.agent_worker:
            worker = AgentRunWorker(
                store,
                _app.state.model_router,
                interval_sec=settings.agent_worker_interval_sec,
            )
            worker.start()
            _app.state.agent_run_worker = worker
        yield
        if worker is not None:
            worker.stop()
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
    app.state.attachment_store = default_attachment_store()
    app.state.agent_definition_store = default_agent_definition_store()
    app.state.agent_run_worker = None
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
            "agent_worker": bool(settings.agent_worker),
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
        """Public: whether the browser must sign in or paste a bearer token."""
        return auth_status(
            mode=auth_mode,
            token_configured=bool(token),
            peer_ip=client_ip(request),
        )

    @app.post("/v1/auth/login")
    def auth_login(body: LoginIn) -> dict[str, Any]:
        """Username/password → opaque session bearer (stored under ~/.ai-lab/)."""
        try:
            return operator_login(body.username, body.password)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc

    @app.post("/v1/auth/logout")
    def auth_logout(
        request: Request,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        """Revoke the current session bearer (no-op for static API token)."""
        _ = request
        if authorization and authorization.startswith("Bearer "):
            revoke_session(authorization[7:].strip())
        return {"ok": True}

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

    @app.get("/v1/conversations")
    def list_conversations(
        request: Request,
        authorization: str | None = Header(default=None),
        limit: int = 50,
    ) -> dict[str, Any]:
        _gate(request, authorization)
        if not hasattr(store, "list_conversations"):
            raise HTTPException(status_code=501, detail="conversation list unavailable")
        items = store.list_conversations(limit=limit)  # type: ignore[attr-defined]
        return {"conversations": [c.to_dict() for c in items]}

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

    @app.delete("/v1/conversations/{conversation_id}")
    def delete_conversation(
        request: Request,
        conversation_id: str,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _gate(request, authorization)
        if not hasattr(store, "delete_conversation"):
            raise HTTPException(status_code=501, detail="conversation delete unavailable")
        ok = store.delete_conversation(conversation_id)  # type: ignore[attr-defined]
        if not ok:
            raise HTTPException(status_code=404, detail="not found")
        return {"ok": True, "id": conversation_id}

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
            meta={
                "kind": "chat_turn",
                "attachment_ids": list(body.attachment_ids or []),
                "deep_research": bool(body.deep_research),
            },
        )
        store.put_message(message)  # type: ignore[attr-defined]

        if not body.reply or role != MessageRole.USER:
            return message.to_dict()

        from .cloud_backends import CloudUnavailable
        from .ollama_backend import OllamaUnavailable

        att_store = app.state.attachment_store
        attachment_ctx = ""
        if body.attachment_ids:
            attachment_ctx = att_store.extract_text_for_prompt(
                conversation_id, list(body.attachment_ids)
            )

        prior = store.list_messages(conversation_id)  # type: ignore[attr-defined]
        lines: list[str] = []
        for m in prior[-12:]:
            lines.append(f"{m.role.value}: {m.content}")
        prompt = "\n".join(lines) if lines else body.content
        if attachment_ctx:
            prompt = prompt + "\n\nAttached materials:\n" + attachment_ctx

        backend = body.backend
        model = body.model
        secrets_s: SecretStore = app.state.secret_store
        if body.deep_research:
            # IWO-028: prefer anthropic then openai when authorized + keyed.
            if secrets_s.usage_billed_authorized():
                if secrets_s.has_provider("anthropic"):
                    backend = "anthropic"
                    model = model if body.backend == "anthropic" else "claude-3-5-haiku-latest"
                elif secrets_s.has_provider("openai"):
                    backend = "openai"
                    model = model if body.backend == "openai" else "gpt-4o-mini"
                else:
                    return {
                        "message": message.to_dict(),
                        "reply": None,
                        "error": "deep_research_requires_frontier_key",
                    }
            else:
                return {
                    "message": message.to_dict(),
                    "reply": None,
                    "error": "deep_research_requires_usage_billed_authorize",
                }

        system = f"You are the {conversation.agent} agent in ai-lab. Reply helpfully and briefly."
        if body.deep_research:
            system = (
                f"You are performing deep research for the {conversation.agent} agent. "
                "Synthesize carefully; note uncertainty; do not invent citations."
            )

        router: ModelRouter = app.state.model_router
        try:
            completion = router.complete(
                CompletionRequest(
                    model=model,
                    prompt=prompt,
                    backend=backend,
                    system=system,
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
                "deep_research": bool(body.deep_research),
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

    @app.post("/v1/conversations/{conversation_id}/messages/stream")
    def stream_message(
        request: Request,
        conversation_id: str,
        body: MessageIn,
        authorization: str | None = Header(default=None),
    ) -> StreamingResponse:
        """SSE chat reply. Prefer Ollama stream; other backends emit one chunk."""
        _gate(request, authorization)
        conversation = store.get_conversation(conversation_id)  # type: ignore[attr-defined]
        if conversation is None:
            raise HTTPException(status_code=404, detail="not found")
        if body.role != "user":
            raise HTTPException(status_code=400, detail="stream only supports role=user")

        from .cloud_backends import CloudUnavailable
        from .ollama_backend import OllamaBackend, OllamaUnavailable

        att_store = app.state.attachment_store
        message = Message.new(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=body.content,
            meta={
                "kind": "chat_turn",
                "attachment_ids": list(body.attachment_ids or []),
                "deep_research": bool(body.deep_research),
            },
        )
        store.put_message(message)  # type: ignore[attr-defined]

        attachment_ctx = ""
        if body.attachment_ids:
            attachment_ctx = att_store.extract_text_for_prompt(
                conversation_id, list(body.attachment_ids)
            )
        prior = store.list_messages(conversation_id)  # type: ignore[attr-defined]
        lines = [f"{m.role.value}: {m.content}" for m in prior[-12:]]
        prompt = "\n".join(lines) if lines else body.content
        if attachment_ctx:
            prompt = prompt + "\n\nAttached materials:\n" + attachment_ctx

        backend = body.backend
        model = body.model
        secrets_s: SecretStore = app.state.secret_store
        if body.deep_research:
            if not secrets_s.usage_billed_authorized():
                raise HTTPException(
                    status_code=400,
                    detail="deep_research_requires_usage_billed_authorize",
                )
            if secrets_s.has_provider("anthropic"):
                backend, model = "anthropic", "claude-3-5-haiku-latest"
            elif secrets_s.has_provider("openai"):
                backend, model = "openai", "gpt-4o-mini"
            else:
                raise HTTPException(status_code=400, detail="deep_research_requires_frontier_key")

        system = f"You are the {conversation.agent} agent in ai-lab. Reply helpfully and briefly."
        if body.deep_research:
            system = (
                f"You are performing deep research for the {conversation.agent} agent. "
                "Synthesize carefully; note uncertainty; do not invent citations."
            )
        req = CompletionRequest(model=model, prompt=prompt, backend=backend, system=system)
        router: ModelRouter = app.state.model_router

        def event_stream():
            yield f"data: {json.dumps({'event': 'user', 'message': message.to_dict()})}\n\n"
            parts: list[str] = []
            metrics: dict[str, Any] = {}
            try:
                backend_obj = router.backends.get(backend)
                if isinstance(backend_obj, OllamaBackend) and hasattr(backend_obj, "stream_complete"):
                    for item in backend_obj.stream_complete(req):
                        if not isinstance(item, dict):
                            # Back-compat if a stub yields plain strings
                            text = str(item)
                            if text:
                                parts.append(text)
                                yield f"data: {json.dumps({'event': 'token', 'text': text})}\n\n"
                            continue
                        text = item.get("text") or ""
                        if text:
                            parts.append(str(text))
                            yield f"data: {json.dumps({'event': 'token', 'text': text})}\n\n"
                        if item.get("done"):
                            eval_count = item.get("eval_count")
                            eval_ns = item.get("eval_duration_ns")
                            tps = None
                            if (
                                isinstance(eval_count, int)
                                and isinstance(eval_ns, int)
                                and eval_ns > 0
                            ):
                                tps = round(eval_count / (eval_ns / 1e9), 2)
                            metrics = {
                                "eval_count": eval_count,
                                "eval_duration_ns": eval_ns,
                                "tokens_per_sec": tps,
                                "source": "ollama",
                            }
                            yield f"data: {json.dumps({'event': 'metrics', **metrics})}\n\n"
                    full = "".join(parts)
                    billing = backend_obj.billing_class.value
                else:
                    completion = router.complete(req)
                    full = completion.text
                    billing = completion.billing_class.value
                    yield f"data: {json.dumps({'event': 'token', 'text': full})}\n\n"
            except (PermissionError, KeyError, OllamaUnavailable, CloudUnavailable) as exc:
                yield f"data: {json.dumps({'event': 'error', 'error': f'provider_unavailable:{exc}'})}\n\n"
                return
            assistant = Message.new(
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT,
                content=full,
                meta={
                    "kind": "chat_reply",
                    "backend": backend,
                    "model": model,
                    "billing_class": billing,
                    "deep_research": bool(body.deep_research),
                    **({"perf": metrics} if metrics else {}),
                },
            )
            store.put_message(assistant)  # type: ignore[attr-defined]
            yield f"data: {json.dumps({'event': 'done', 'reply': assistant.to_dict()})}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    @app.post("/v1/conversations/{conversation_id}/attachments")
    async def upload_attachment(
        request: Request,
        conversation_id: str,
        authorization: str | None = Header(default=None),
        file: UploadFile = File(...),
    ) -> dict[str, Any]:
        _gate(request, authorization)
        conversation = store.get_conversation(conversation_id)  # type: ignore[attr-defined]
        if conversation is None:
            raise HTTPException(status_code=404, detail="not found")
        raw = await file.read()
        try:
            meta = app.state.attachment_store.save(
                conversation_id=conversation_id,
                filename=file.filename or "upload.bin",
                data=raw,
                content_type=file.content_type or "",
            )
        except AttachmentError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return meta

    @app.get("/v1/mcp/status")
    def mcp_status(
        request: Request,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _gate(request, authorization)
        return mcp_client_status()

    @app.put("/v1/mcp/servers/{server_id}")
    def put_mcp_server(
        request: Request,
        server_id: str,
        body: McpServerIn,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        """Register or update a local MCP connection (~/.ai-lab/mcp-servers.json)."""
        _gate(request, authorization)
        if body.id and body.id != server_id:
            raise HTTPException(status_code=400, detail="id mismatch")
        try:
            return upsert_local_server(
                server_id=server_id,
                label=body.label,
                transport=body.transport,
                command=body.command,
                args=body.args,
                enabled=body.enabled,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.delete("/v1/mcp/servers/{server_id}")
    def remove_mcp_server(
        request: Request,
        server_id: str,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _gate(request, authorization)
        if not delete_local_server(server_id):
            raise HTTPException(status_code=404, detail="not found")
        return {"ok": True, "id": server_id}

    @app.get("/v1/mcp/servers/{server_id}/tools")
    def mcp_server_tools(
        request: Request,
        server_id: str,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        """List tools from a local stdio MCP server (IWO-029)."""
        _gate(request, authorization)
        try:
            tools = list_mcp_tools(server_id)
        except McpDenied as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except McpTransportError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"server_id": server_id, "tools": tools}

    @app.get("/v1/agent-runs")
    def list_all_agent_runs(
        request: Request,
        authorization: str | None = Header(default=None),
        limit: int = 40,
    ) -> dict[str, Any]:
        """Recent agent-loop runs across conversations (Studio Runs view)."""
        _gate(request, authorization)
        if not hasattr(store, "list_agent_runs"):
            raise HTTPException(status_code=501, detail="agent runs unavailable")
        runs = store.list_agent_runs(None)  # type: ignore[attr-defined]
        lim = max(1, min(int(limit), 100))
        newest = list(reversed(runs))[:lim]
        return {"runs": [r.to_dict() for r in newest]}

    @app.post("/v1/agent-runs/worker/tick")
    def worker_tick(
        request: Request,
        authorization: str | None = Header(default=None),
        limit: int = 1,
    ) -> dict[str, Any]:
        """Drain up to ``limit`` queued agent runs (ops / tests / no in-process worker)."""
        _gate(request, authorization)
        return drain_queued_runs(
            store,
            app.state.model_router,
            limit=max(1, min(limit, 8)),
        )

    @app.get("/v1/agent-definitions")
    def list_agent_definitions(
        request: Request,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _gate(request, authorization)
        items = app.state.agent_definition_store.list()
        return {"definitions": [d.to_dict() for d in items]}

    @app.post("/v1/agent-definitions")
    def create_agent_definition(
        request: Request,
        body: AgentDefinitionIn,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _gate(request, authorization)
        try:
            load_policy(body.agent)
        except (OSError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if body.mcp_server_ids:
            try:
                require_mcp_servers(body.mcp_server_ids)
            except McpDenied as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
        if body.schedule_cron.strip():
            try:
                parse_cron(body.schedule_cron.strip())
            except CronError as exc:
                raise HTTPException(status_code=400, detail=f"invalid schedule_cron: {exc}") from exc
        definition = AgentDefinition.new(
            title=body.title,
            agent=body.agent,
            system_prompt=body.system_prompt,
            tools=body.tools,
            mcp_server_ids=body.mcp_server_ids,
            schedule_cron=body.schedule_cron,
        )
        app.state.agent_definition_store.put(definition)
        return definition.to_dict()

    @app.get("/v1/agent-definitions/{definition_id}")
    def get_agent_definition(
        request: Request,
        definition_id: str,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _gate(request, authorization)
        definition = app.state.agent_definition_store.get(definition_id)
        if definition is None:
            raise HTTPException(status_code=404, detail="not found")
        return definition.to_dict()

    def _run_definition(
        definition: AgentDefinition,
        *,
        objective: str = "",
        model: str = "llama3.2:3b",
        backend: str = "ollama",
        billing_class: str = "local",
        max_steps: int = 8,
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        if definition.mcp_server_ids:
            require_mcp_servers(definition.mcp_server_ids)
        conv_id = conversation_id
        if not conv_id:
            conversation = Conversation.new(
                agent=definition.agent, title=f"agent:{definition.title}"
            )
            store.put_conversation(conversation)  # type: ignore[attr-defined]
            conv_id = conversation.id
        else:
            conversation = store.get_conversation(conv_id)  # type: ignore[attr-defined]
            if conversation is None:
                raise HTTPException(status_code=404, detail="conversation not found")
        from .conversation import RunBudget

        objective_text = objective or definition.system_prompt or definition.title
        run = AgentRun.new(
            agent=definition.agent,
            objective=objective_text,
            conversation_id=conv_id,
            model=model,
            billing_class=BillingClass(billing_class),
            backend=backend,
            budget=RunBudget(max_steps=max_steps),
            mcp_server_ids=list(definition.mcp_server_ids or []),
        )
        run.status = AgentRunStatus.QUEUED
        store.put_agent_run(run)  # type: ignore[attr-defined]
        out = run.to_dict()
        out["agent_definition_id"] = definition.id
        out["note"] = "Queued for background worker (FEAT-002 / IWO-031)."
        return out

    @app.get("/v1/scheduler/status")
    def get_scheduler_status(
        request: Request,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _gate(request, authorization)
        defs = [
            {
                "id": d.id,
                "title": d.title,
                "schedule_cron": d.schedule_cron,
            }
            for d in app.state.agent_definition_store.list()
            if (d.schedule_cron or "").strip()
        ]
        out = scheduler_status()
        out["scheduled_definitions"] = defs
        return out

    @app.post("/v1/scheduler/tick")
    def post_scheduler_tick(
        request: Request,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        """Evaluate due agent-definition cron schedules and start bounded runs."""
        _gate(request, authorization)

        def runner(definition: AgentDefinition) -> dict[str, Any]:
            return _run_definition(definition)

        return scheduler_tick(app.state.agent_definition_store, run_definition=runner)

    @app.post("/v1/agent-definitions/{definition_id}/runs")
    def run_agent_definition(
        request: Request,
        definition_id: str,
        body: AgentDefinitionRunIn,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        """Run a deployed personal agent via the existing bounded loop."""
        _gate(request, authorization)
        definition = app.state.agent_definition_store.get(definition_id)
        if definition is None:
            raise HTTPException(status_code=404, detail="not found")
        try:
            return _run_definition(
                definition,
                objective=body.objective,
                model=body.model,
                backend=body.backend,
                billing_class=body.billing_class,
                max_steps=body.max_steps,
                conversation_id=body.conversation_id,
            )
        except McpDenied as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

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
        if body.execute:
            run.status = AgentRunStatus.QUEUED
            store.put_agent_run(run)  # type: ignore[attr-defined]
            out = run.to_dict()
            out["kind"] = "agent_run"
            out["note"] = (
                "Queued for background worker. Poll GET /v1/agent-runs/{id} "
                "or wait for AI_LAB_AGENT_WORKER. POST /v1/agent-runs/worker/tick to drain."
            )
            return out
        run.status = AgentRunStatus.CREATED
        store.put_agent_run(run)  # type: ignore[attr-defined]
        out = run.to_dict()
        out["kind"] = "agent_run"
        out["note"] = (
            "Durable agent run created (not executing). Set execute=true to enqueue "
            "the mini model/tool loop."
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
        out = run.to_dict()
        out["note"] = "Re-queued for background worker."
        return out

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
