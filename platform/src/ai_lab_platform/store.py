"""Durable store protocol + SQLite implementation for tests."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Protocol

from .state_machine import transition
from .work_order import Status, WorkOrder, utcnow


class WorkOrderStore(Protocol):
    def put(self, order: WorkOrder) -> None: ...
    def get(self, order_id: str) -> WorkOrder | None: ...
    def list(self, status: Status | None = None) -> list[WorkOrder]: ...
    def set_status(self, order_id: str, status: Status) -> WorkOrder: ...


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
