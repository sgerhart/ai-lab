"""Durable adapters for security events. References existing IDs; does not copy their tables."""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Protocol

from .events import SecurityEvent

_SQLITE_DDL = """
CREATE TABLE IF NOT EXISTS security_events (
    id TEXT PRIMARY KEY,
    occurred_at TEXT NOT NULL,
    agent_id TEXT NOT NULL DEFAULT '',
    run_id TEXT NOT NULL DEFAULT '',
    job_id TEXT NOT NULL DEFAULT '',
    tool TEXT NOT NULL DEFAULT '',
    payload TEXT NOT NULL
)
"""


class EventLog(Protocol):
    def append(self, event: SecurityEvent) -> None: ...

    def list(
        self,
        *,
        agent_id: str = "",
        run_id: str = "",
        job_id: str = "",
    ) -> list[SecurityEvent]: ...


class MemoryEventLog:
    def __init__(self) -> None:
        self._events: list[SecurityEvent] = []

    def append(self, event: SecurityEvent) -> None:
        event.to_dict()
        self._events.append(event)

    def list(
        self,
        *,
        agent_id: str = "",
        run_id: str = "",
        job_id: str = "",
    ) -> list[SecurityEvent]:
        return [
            event
            for event in self._events
            if (not agent_id or event.agent_id == agent_id)
            and (not run_id or event.run_id == run_id)
            and (not job_id or event.job_id == job_id)
        ]


class SqliteEventLog:
    def __init__(self, path: str) -> None:
        self.path = path
        with self._connect() as conn:
            conn.execute(_SQLITE_DDL)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def append(self, event: SecurityEvent) -> None:
        body = event.to_dict()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO security_events (id, occurred_at, agent_id, run_id, job_id, tool, payload)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET payload = excluded.payload
                """,
                (
                    event.event_id,
                    event.occurred_at,
                    event.agent_id,
                    event.run_id,
                    event.job_id,
                    event.tool,
                    json.dumps(body),
                ),
            )

    def list(
        self,
        *,
        agent_id: str = "",
        run_id: str = "",
        job_id: str = "",
    ) -> list[SecurityEvent]:
        query = "SELECT payload FROM security_events WHERE 1 = 1"
        args: list[str] = []
        if agent_id:
            query += " AND agent_id = ?"
            args.append(agent_id)
        if run_id:
            query += " AND run_id = ?"
            args.append(run_id)
        if job_id:
            query += " AND job_id = ?"
            args.append(job_id)
        query += " ORDER BY occurred_at"
        with self._connect() as conn:
            rows = conn.execute(query, args).fetchall()
        return [SecurityEvent.from_dict(json.loads(row["payload"])) for row in rows]


class PostgresEventLog:
    """Writes the same envelope into the control-plane database. No network beyond that DSN."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self._ensure()

    def _connect(self) -> Any:
        import psycopg

        return psycopg.connect(self.dsn, autocommit=True)

    def _ensure(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS security_events (
                    id TEXT PRIMARY KEY,
                    occurred_at TIMESTAMPTZ NOT NULL,
                    agent_id TEXT NOT NULL DEFAULT '',
                    run_id TEXT NOT NULL DEFAULT '',
                    job_id TEXT NOT NULL DEFAULT '',
                    tool TEXT NOT NULL DEFAULT '',
                    payload JSONB NOT NULL
                )
                """
            )

    def append(self, event: SecurityEvent) -> None:
        from psycopg.types.json import Jsonb

        body = event.to_dict()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO security_events (id, occurred_at, agent_id, run_id, job_id, tool, payload)
                VALUES (%s, %s::timestamptz, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET payload = EXCLUDED.payload
                """,
                (
                    event.event_id,
                    event.occurred_at,
                    event.agent_id,
                    event.run_id,
                    event.job_id,
                    event.tool,
                    Jsonb(body),
                ),
            )

    def list(
        self,
        *,
        agent_id: str = "",
        run_id: str = "",
        job_id: str = "",
    ) -> list[SecurityEvent]:
        query = "SELECT payload FROM security_events WHERE 1 = 1"
        args: list[str] = []
        if agent_id:
            query += " AND agent_id = %s"
            args.append(agent_id)
        if run_id:
            query += " AND run_id = %s"
            args.append(run_id)
        if job_id:
            query += " AND job_id = %s"
            args.append(job_id)
        query += " ORDER BY occurred_at"
        with self._connect() as conn:
            rows = conn.execute(query, args).fetchall()
        events: list[SecurityEvent] = []
        for row in rows:
            payload = row[0]
            if isinstance(payload, str):
                payload = json.loads(payload)
            events.append(SecurityEvent.from_dict(payload))
        return events


def event_log_for_store(store: object) -> EventLog:
    path = getattr(store, "path", None)
    if isinstance(path, str) and path:
        return SqliteEventLog(path)
    dsn = getattr(store, "dsn", None)
    if isinstance(dsn, str) and dsn:
        return PostgresEventLog(dsn)
    return MemoryEventLog()
