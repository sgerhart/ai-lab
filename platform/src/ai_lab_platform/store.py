"""Durable store protocol + SQLite implementation for tests."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Protocol

from .conversation import AgentRun, Conversation, Message, Project
from .state_machine import transition
from .work_order import Status, WorkOrder, utcnow


class WorkOrderStore(Protocol):
    def put(self, order: WorkOrder) -> None: ...
    def get(self, order_id: str) -> WorkOrder | None: ...
    def list(self, status: Status | None = None) -> list[WorkOrder]: ...
    def set_status(self, order_id: str, status: Status) -> WorkOrder: ...
    def append_audit(self, work_order_id: str, actor: str, event: str, detail: dict | None = None) -> None: ...


class ConversationStore(Protocol):
    def put_conversation(self, conversation: Conversation) -> None: ...
    def get_conversation(self, conversation_id: str) -> Conversation | None: ...
    def list_conversations(self, *, limit: int = 50) -> list[Conversation]: ...
    def delete_conversation(self, conversation_id: str) -> bool: ...
    def put_message(self, message: Message) -> None: ...
    def list_messages(self, conversation_id: str) -> list[Message]: ...
    def put_agent_run(self, run: AgentRun) -> None: ...
    def get_agent_run(self, run_id: str) -> AgentRun | None: ...
    def list_agent_runs(self, conversation_id: str | None = None) -> list[AgentRun]: ...


class SqliteStore:
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS work_orders (
                    id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    work_order_id TEXT NOT NULL,
                    at TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    event TEXT NOT NULL,
                    detail TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversation_messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_runs (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def put(self, order: WorkOrder) -> None:
        order.updated_at = utcnow()
        blob = json.dumps(order.to_dict())
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO work_orders (id, payload, status, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    payload = excluded.payload,
                    status = excluded.status,
                    updated_at = excluded.updated_at
                """,
                (order.id, blob, order.status.value, order.updated_at),
            )

    def get(self, order_id: str) -> WorkOrder | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM work_orders WHERE id = ?", (order_id,)
            ).fetchone()
        if row is None:
            return None
        return WorkOrder.from_dict(json.loads(row["payload"]))

    def list(self, status: Status | None = None) -> list[WorkOrder]:
        query = "SELECT payload FROM work_orders"
        args: tuple[str, ...] = ()
        if status is not None:
            query += " WHERE status = ?"
            args = (status.value,)
        with self._connect() as conn:
            rows = conn.execute(query, args).fetchall()
        return [WorkOrder.from_dict(json.loads(r["payload"])) for r in rows]

    def set_status(self, order_id: str, status: Status) -> WorkOrder:
        order = self.get(order_id)
        if order is None:
            raise KeyError(order_id)
        order.status = transition(order.status, status)
        self.put(order)
        return order

    def append_audit(
        self, work_order_id: str, actor: str, event: str, detail: dict | None = None
    ) -> None:
        blob = json.dumps(detail or {})
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO audit_events (work_order_id, at, actor, event, detail)
                VALUES (?, ?, ?, ?, ?)
                """,
                (work_order_id, utcnow(), actor, event, blob),
            )

    def list_audit(self, work_order_id: str) -> list[dict[str, str]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT at, actor, event, detail FROM audit_events WHERE work_order_id = ? ORDER BY id",
                (work_order_id,),
            ).fetchall()
        out: list[dict[str, str]] = []
        for row in rows:
            out.append(
                {
                    "at": row["at"],
                    "actor": row["actor"],
                    "event": row["event"],
                    "detail": row["detail"],
                }
            )
        return out

    def put_conversation(self, conversation: Conversation) -> None:
        conversation.updated_at = utcnow()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO conversations (id, payload, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    payload = excluded.payload,
                    updated_at = excluded.updated_at
                """,
                (conversation.id, json.dumps(conversation.to_dict()), conversation.updated_at),
            )

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM conversations WHERE id = ?", (conversation_id,)
            ).fetchone()
        if row is None:
            return None
        return Conversation.from_dict(json.loads(row["payload"]))

    def list_conversations(self, *, limit: int = 50) -> list[Conversation]:
        lim = max(1, min(int(limit), 200))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT payload FROM conversations
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (lim,),
            ).fetchall()
        return [Conversation.from_dict(json.loads(r["payload"])) for r in rows]

    def delete_conversation(self, conversation_id: str) -> bool:
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM conversation_messages WHERE conversation_id = ?",
                (conversation_id,),
            )
            cur = conn.execute(
                "DELETE FROM conversations WHERE id = ?", (conversation_id,)
            )
            return cur.rowcount > 0

    def put_message(self, message: Message) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO conversation_messages (id, conversation_id, payload, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    payload = excluded.payload,
                    created_at = excluded.created_at
                """,
                (
                    message.id,
                    message.conversation_id,
                    json.dumps(message.to_dict()),
                    message.created_at,
                ),
            )
            conn.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (utcnow(), message.conversation_id),
            )

    def list_messages(self, conversation_id: str) -> list[Message]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT payload FROM conversation_messages
                WHERE conversation_id = ?
                ORDER BY created_at, id
                """,
                (conversation_id,),
            ).fetchall()
        return [Message.from_dict(json.loads(r["payload"])) for r in rows]

    def put_project(self, project: Project) -> None:
        project.updated_at = utcnow()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO projects (id, payload, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    payload = excluded.payload,
                    updated_at = excluded.updated_at
                """,
                (project.id, json.dumps(project.to_dict()), project.updated_at),
            )

    def get_project(self, project_id: str) -> Project | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM projects WHERE id = ?", (project_id,)
            ).fetchone()
        if row is None:
            return None
        return Project.from_dict(json.loads(row["payload"]))

    def list_projects(self) -> list[Project]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload FROM projects ORDER BY updated_at DESC"
            ).fetchall()
        return [Project.from_dict(json.loads(row["payload"])) for row in rows]

    def delete_project(self, project_id: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            return cur.rowcount > 0

    def put_agent_run(self, run: AgentRun) -> None:
        run.updated_at = utcnow()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO agent_runs (id, conversation_id, payload, status, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    conversation_id = excluded.conversation_id,
                    payload = excluded.payload,
                    status = excluded.status,
                    updated_at = excluded.updated_at
                """,
                (
                    run.id,
                    run.conversation_id,
                    json.dumps(run.to_dict()),
                    run.status.value,
                    run.updated_at,
                ),
            )

    def get_agent_run(self, run_id: str) -> AgentRun | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM agent_runs WHERE id = ?", (run_id,)
            ).fetchone()
        if row is None:
            return None
        return AgentRun.from_dict(json.loads(row["payload"]))

    def list_agent_runs(self, conversation_id: str | None = None) -> list[AgentRun]:
        query = "SELECT payload FROM agent_runs"
        args: tuple[str, ...] = ()
        if conversation_id is not None:
            query += " WHERE conversation_id = ?"
            args = (conversation_id,)
        query += " ORDER BY updated_at"
        with self._connect() as conn:
            rows = conn.execute(query, args).fetchall()
        return [AgentRun.from_dict(json.loads(r["payload"])) for r in rows]
