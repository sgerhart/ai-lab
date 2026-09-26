"""Personal agent definitions (FEAT-013 / IWO-026). Durable configs, not chat turns."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from .work_order import utcnow


@dataclass
class AgentDefinition:
    id: str
    title: str
    agent: str = "lab-operations"
    system_prompt: str = ""
    tools: list[str] = field(default_factory=list)
    mcp_server_ids: list[str] = field(default_factory=list)
    schedule_cron: str = ""
    studio: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utcnow)
    updated_at: str = field(default_factory=utcnow)

    @classmethod
    def new(
        cls,
        *,
        title: str,
        agent: str = "lab-operations",
        system_prompt: str = "",
        tools: list[str] | None = None,
        mcp_server_ids: list[str] | None = None,
        schedule_cron: str = "",
        studio: dict[str, Any] | None = None,
    ) -> AgentDefinition:
        return cls(
            id=str(uuid4()),
            title=title.strip() or "untitled",
            agent=agent,
            system_prompt=system_prompt,
            tools=list(tools or []),
            mcp_server_ids=list(mcp_server_ids or []),
            schedule_cron=schedule_cron.strip(),
            studio=dict(studio or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentDefinition:
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in known})


class AgentDefinitionStore:
    """SQLite file under ~/.ai-lab for agent definitions (Postgres later)."""

    def __init__(self, path: str | Path | None = None) -> None:
        if path is None:
            path = Path.home() / ".ai-lab" / "agent-definitions.sqlite"
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_definitions (
                    id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def put(self, definition: AgentDefinition) -> None:
        definition.updated_at = utcnow()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO agent_definitions (id, payload, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    payload = excluded.payload,
                    updated_at = excluded.updated_at
                """,
                (definition.id, json.dumps(definition.to_dict()), definition.updated_at),
            )

    def get(self, definition_id: str) -> AgentDefinition | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM agent_definitions WHERE id = ?", (definition_id,)
            ).fetchone()
        if row is None:
            return None
        return AgentDefinition.from_dict(json.loads(row["payload"]))

    def list(self, *, limit: int = 50) -> list[AgentDefinition]:
        lim = max(1, min(int(limit), 200))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT payload FROM agent_definitions
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (lim,),
            ).fetchall()
        return [AgentDefinition.from_dict(json.loads(r["payload"])) for r in rows]

    def delete(self, definition_id: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute(
                "DELETE FROM agent_definitions WHERE id = ?", (definition_id,)
            )
            return cur.rowcount > 0


def default_agent_definition_store() -> AgentDefinitionStore:
    return AgentDefinitionStore()
