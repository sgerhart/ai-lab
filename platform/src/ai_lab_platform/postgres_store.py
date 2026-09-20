"""PostgreSQL work-order store. Authoritative on the M1 control plane."""

from __future__ import annotations

import json
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb

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
