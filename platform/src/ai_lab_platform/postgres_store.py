"""PostgreSQL work-order store. Authoritative on the M1 control plane."""

from __future__ import annotations

import json
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb

from .conversation import AgentRun, Conversation, Message
from .state_machine import transition
from .work_order import Status, WorkOrder, utcnow

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def _sql_statements(sql: str) -> list[str]:
    out: list[str] = []
    for raw in sql.split(";"):
        lines = [line for line in raw.splitlines() if line.strip() and not line.strip().startswith("--")]
        stmt = "\n".join(lines).strip()
        if stmt:
            out.append(stmt)
    return out


class PostgresStore:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self._init()

    def _connect(self) -> psycopg.Connection:
        return psycopg.connect(self.dsn, autocommit=True)

    def _init(self) -> None:
        sql = SCHEMA_PATH.read_text(encoding="utf-8")
        with self._connect() as conn:
            for statement in _sql_statements(sql):
                conn.execute(statement)

    def put(self, order: WorkOrder) -> None:
        order.updated_at = utcnow()
        payload = order.to_dict()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO work_orders (id, objective, agent, status, payload, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s::timestamptz, %s::timestamptz)
                ON CONFLICT (id) DO UPDATE SET
                    objective = EXCLUDED.objective,
                    agent = EXCLUDED.agent,
                    status = EXCLUDED.status,
                    payload = EXCLUDED.payload,
                    updated_at = EXCLUDED.updated_at
                """,
                (
                    order.id,
                    order.objective,
                    order.agent,
                    order.status.value,
                    Jsonb(payload),
                    order.created_at,
                    order.updated_at,
                ),
            )

    def get(self, order_id: str) -> WorkOrder | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM work_orders WHERE id = %s", (order_id,)
            ).fetchone()
        if row is None:
            return None
        payload = row[0]
        if isinstance(payload, str):
            payload = json.loads(payload)
        return WorkOrder.from_dict(payload)

    def list(self, status: Status | None = None) -> list[WorkOrder]:
        query = "SELECT payload FROM work_orders"
        args: tuple[str, ...] = ()
        if status is not None:
            query += " WHERE status = %s"
            args = (status.value,)
        with self._connect() as conn:
            rows = conn.execute(query, args).fetchall()
        out: list[WorkOrder] = []
        for row in rows:
            payload = row[0]
            if isinstance(payload, str):
                payload = json.loads(payload)
            out.append(WorkOrder.from_dict(payload))
        return out

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
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO audit_events (work_order_id, actor, event, detail)
                VALUES (%s, %s, %s, %s)
                """,
                (work_order_id, actor, event, Jsonb(detail or {})),
            )

    def list_audit(self, work_order_id: str) -> list[dict[str, object]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT at, actor, event, detail
                FROM audit_events
                WHERE work_order_id = %s
                ORDER BY id
                """,
                (work_order_id,),
            ).fetchall()
        out: list[dict[str, object]] = []
        for row in rows:
            out.append({"at": row[0], "actor": row[1], "event": row[2], "detail": row[3]})
        return out

    def put_conversation(self, conversation: Conversation) -> None:
        conversation.updated_at = utcnow()
        payload = conversation.to_dict()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO conversations (id, agent, title, payload, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s::timestamptz, %s::timestamptz)
                ON CONFLICT (id) DO UPDATE SET
                    agent = EXCLUDED.agent,
                    title = EXCLUDED.title,
                    payload = EXCLUDED.payload,
                    updated_at = EXCLUDED.updated_at
                """,
                (
                    conversation.id,
                    conversation.agent,
                    conversation.title,
                    Jsonb(payload),
                    conversation.created_at,
                    conversation.updated_at,
                ),
            )

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM conversations WHERE id = %s", (conversation_id,)
            ).fetchone()
        if row is None:
            return None
        payload = row[0]
        if isinstance(payload, str):
            payload = json.loads(payload)
        return Conversation.from_dict(payload)

    def put_message(self, message: Message) -> None:
        payload = message.to_dict()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO conversation_messages (id, conversation_id, role, content, payload, created_at)
                VALUES (%s, %s, %s, %s, %s, %s::timestamptz)
                ON CONFLICT (id) DO UPDATE SET
                    role = EXCLUDED.role,
                    content = EXCLUDED.content,
                    payload = EXCLUDED.payload
                """,
                (
                    message.id,
                    message.conversation_id,
                    message.role.value,
                    message.content,
                    Jsonb(payload),
                    message.created_at,
                ),
            )
            conn.execute(
                "UPDATE conversations SET updated_at = now() WHERE id = %s",
                (message.conversation_id,),
            )

    def list_messages(self, conversation_id: str) -> list[Message]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT payload FROM conversation_messages
                WHERE conversation_id = %s
                ORDER BY created_at, id
                """,
                (conversation_id,),
            ).fetchall()
        out: list[Message] = []
        for row in rows:
            payload = row[0]
            if isinstance(payload, str):
                payload = json.loads(payload)
            out.append(Message.from_dict(payload))
        return out

    def put_agent_run(self, run: AgentRun) -> None:
        run.updated_at = utcnow()
        payload = run.to_dict()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO agent_runs (
                    id, conversation_id, work_order_id, agent, status, payload, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s::timestamptz, %s::timestamptz)
                ON CONFLICT (id) DO UPDATE SET
                    conversation_id = EXCLUDED.conversation_id,
                    work_order_id = EXCLUDED.work_order_id,
                    agent = EXCLUDED.agent,
                    status = EXCLUDED.status,
                    payload = EXCLUDED.payload,
                    updated_at = EXCLUDED.updated_at
                """,
                (
                    run.id,
                    run.conversation_id,
                    run.work_order_id,
                    run.agent,
                    run.status.value,
                    Jsonb(payload),
                    run.created_at,
                    run.updated_at,
                ),
            )

    def get_agent_run(self, run_id: str) -> AgentRun | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM agent_runs WHERE id = %s", (run_id,)
            ).fetchone()
        if row is None:
            return None
        payload = row[0]
        if isinstance(payload, str):
            payload = json.loads(payload)
        return AgentRun.from_dict(payload)

    def list_agent_runs(self, conversation_id: str | None = None) -> list[AgentRun]:
        query = "SELECT payload FROM agent_runs"
        args: tuple[str, ...] = ()
        if conversation_id is not None:
            query += " WHERE conversation_id = %s"
            args = (conversation_id,)
        query += " ORDER BY updated_at"
        with self._connect() as conn:
            rows = conn.execute(query, args).fetchall()
        out: list[AgentRun] = []
        for row in rows:
            payload = row[0]
            if isinstance(payload, str):
                payload = json.loads(payload)
            out.append(AgentRun.from_dict(payload))
        return out
