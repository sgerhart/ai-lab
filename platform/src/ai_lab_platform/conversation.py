"""Conversation and agent-run records (FEAT-010 / IWO-002).

Ordinary chat messages are **not** runtime work orders and are **not**
Implementation Work Orders. An agent run is a durable execution of the
personal-agent loop (or a placeholder until IWO-005 lands the model/tool
graph). A run may optionally reference a runtime work-order UUID.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4

from .work_order import utcnow


class BillingClass(str, Enum):
    """ADR 0038 — must be visible wherever a model is selected."""

    LOCAL = "local"
    SUBSCRIPTION_CLIENT = "subscription_client"
    USAGE_BILLED_API = "usage_billed_api"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class AgentRunStatus(str, Enum):
    """Agent-run lifecycle. Distinct from implementation IWO states and from
    WorkOrder.Status, though values overlap for operator familiarity."""

    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class RunBudget:
    max_steps: int = 32
    max_time_seconds: int = 3600
    max_tokens: int | None = None
    max_cost_usd: float | None = None


@dataclass
class Project:
    """A named group of chats. Organization only — not a work order."""

    id: str
    name: str
    description: str = ""
    created_at: str = field(default_factory=utcnow)
    updated_at: str = field(default_factory=utcnow)

    @classmethod
    def new(cls, *, name: str, description: str = "") -> Project:
        return cls(id=str(uuid4()), name=name.strip(), description=description.strip())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Project:
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class Conversation:
    id: str
    agent: str
    title: str = ""
    project_id: str = ""
    created_at: str = field(default_factory=utcnow)
    updated_at: str = field(default_factory=utcnow)

    @classmethod
    def new(cls, *, agent: str, title: str = "") -> Conversation:
        return cls(id=str(uuid4()), agent=agent, title=title)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Conversation:
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class Message:
    id: str
    conversation_id: str
    role: MessageRole
    content: str
    created_at: str = field(default_factory=utcnow)
    # Ordinary chat turn metadata only — not an approval or IWO record.
    meta: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def new(
        cls,
        *,
        conversation_id: str,
        role: MessageRole | str,
        content: str,
        meta: dict[str, Any] | None = None,
    ) -> Message:
        role_enum = role if isinstance(role, MessageRole) else MessageRole(role)
        return cls(
            id=str(uuid4()),
            conversation_id=conversation_id,
            role=role_enum,
            content=content,
            meta=meta or {},
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["role"] = self.role.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Message:
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        payload = {k: v for k, v in data.items() if k in known}
        payload["role"] = MessageRole(payload["role"])
        payload.setdefault("meta", {})
        return cls(**payload)


@dataclass
class AgentRun:
    id: str
    agent: str
    status: AgentRunStatus = AgentRunStatus.CREATED
    conversation_id: str | None = None
    # Optional link to a runtime Postgres work order (UUID). Not an IWO id.
    work_order_id: str | None = None
    objective: str = ""
    model: str = "fake-instruct"
    billing_class: BillingClass = BillingClass.LOCAL
    backend: str = "fake"
    budget: RunBudget = field(default_factory=RunBudget)
    # Placeholder / loop traces (IWO-002 / IWO-005).
    traces: list[dict[str, Any]] = field(default_factory=list)
    usage: dict[str, Any] = field(default_factory=dict)
    # IWO-007: specific tool action awaiting human decision.
    pending_action: dict[str, Any] | None = None
    error: str | None = None
    final_result: str | None = None
    # MCP servers this run may call (IWO-029). Empty = built-in tools only.
    mcp_server_ids: list[str] = field(default_factory=list)
    # Isolated git worktree for coding writes. Empty = the control-plane checkout (read tools only).
    workspace_root: str = ""
    created_at: str = field(default_factory=utcnow)
    updated_at: str = field(default_factory=utcnow)

    @classmethod
    def new(
        cls,
        *,
        agent: str,
        objective: str = "",
        conversation_id: str | None = None,
        work_order_id: str | None = None,
        model: str = "fake-instruct",
        billing_class: BillingClass | str = BillingClass.LOCAL,
        backend: str = "fake",
        budget: RunBudget | dict[str, Any] | None = None,
        mcp_server_ids: list[str] | None = None,
        workspace_root: str = "",
    ) -> AgentRun:
        bc = (
            billing_class
            if isinstance(billing_class, BillingClass)
            else BillingClass(billing_class)
        )
        if budget is None:
            bud = RunBudget()
        elif isinstance(budget, dict):
            bud = RunBudget(**budget)
        else:
            bud = budget
        return cls(
            id=str(uuid4()),
            agent=agent,
            objective=objective,
            conversation_id=conversation_id,
            work_order_id=work_order_id,
            model=model,
            billing_class=bc,
            backend=backend,
            budget=bud,
            mcp_server_ids=list(mcp_server_ids or []),
            workspace_root=workspace_root,
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["billing_class"] = self.billing_class.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentRun:
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        payload = {k: v for k, v in data.items() if k in known}
        payload["status"] = AgentRunStatus(payload["status"])
        payload["billing_class"] = BillingClass(payload["billing_class"])
        budget = payload.get("budget") or {}
        payload["budget"] = RunBudget(**budget) if isinstance(budget, dict) else budget
        payload.setdefault("traces", [])
        payload.setdefault("usage", {})
        payload.setdefault("pending_action", None)
        payload.setdefault("mcp_server_ids", [])
        payload.setdefault("workspace_root", "")
        return cls(**payload)
