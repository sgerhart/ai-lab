"""Work-order record. PostgreSQL is authoritative in production; this is the in-process shape."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class Status(str, Enum):
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


TERMINAL = frozenset({Status.COMPLETED, Status.CANCELLED})


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Attempt:
    index: int
    started_at: str
    ended_at: str | None = None
    error: str | None = None


@dataclass
class ExecutionPolicy:
    max_attempts: int = 3
    timeout_seconds: int = 3600
    retry_on_interrupt: bool = True


@dataclass
class WorkOrder:
    id: str
    objective: str
    agent: str
    status: Status = Status.CREATED
    input_references: list[str] = field(default_factory=list)
    bounded_scope: str = ""
    allowed_tools: list[str] = field(default_factory=list)
    execution_policy: ExecutionPolicy = field(default_factory=ExecutionPolicy)
    approval_requirements: list[str] = field(default_factory=list)
    attempt_history: list[Attempt] = field(default_factory=list)
    log_refs: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    completion_criteria: str = ""
    final_result: str | None = None
    approved_tools: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utcnow)
    updated_at: str = field(default_factory=utcnow)

    @classmethod
    def new(cls, *, objective: str, agent: str, **kwargs: Any) -> WorkOrder:
        return cls(id=str(uuid4()), objective=objective, agent=agent, **kwargs)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkOrder:
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        payload = {k: v for k, v in data.items() if k in known}
        payload["status"] = Status(payload["status"])
        policy = payload.get("execution_policy") or {}
        payload["execution_policy"] = ExecutionPolicy(**policy) if isinstance(policy, dict) else policy
        attempts = []
        for item in payload.get("attempt_history") or []:
            attempts.append(Attempt(**item) if isinstance(item, dict) else item)
        payload["attempt_history"] = attempts
        payload.setdefault("approved_tools", [])
        return cls(**payload)
