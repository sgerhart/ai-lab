"""Durable job store and state machine for controller operations."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import threading
import time
from typing import Any

from packages.contracts import (
    AuditEvent,
    ExecutionResult,
    RewardResult,
)


class JobStore:
    """Thread-safe SQLite store for durable execution jobs, candidates, and audit records."""

    def __init__(self, db_path: str | Path = ":memory:"):
        self.db_path = str(db_path)
        self._lock = threading.Lock()
        if self.db_path == ":memory:":
            self._shared_conn: sqlite3.Connection | None = sqlite3.connect(
                ":memory:", check_same_thread=False
            )
            self._shared_conn.row_factory = sqlite3.Row
        else:
            self._shared_conn = None
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self._shared_conn is not None:
            return self._shared_conn
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._lock, self._get_connection() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS execution_jobs (
                job_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                state TEXT NOT NULL,
                lease_owner TEXT,
                lease_expires_at REAL,
                retry_count INTEGER DEFAULT 0,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS candidates (
                candidate_sha256 TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                prompt TEXT NOT NULL,
                code TEXT NOT NULL,
                model_name TEXT NOT NULL,
                syntax_valid INTEGER NOT NULL,
                prompt_tokens INTEGER DEFAULT 0,
                completion_tokens INTEGER DEFAULT 0,
                created_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS executions (
                execution_id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                candidate_sha256 TEXT NOT NULL,
                test_bundle_sha256 TEXT NOT NULL,
                status TEXT NOT NULL,
                passed INTEGER NOT NULL,
                total INTEGER NOT NULL,
                elapsed_ms INTEGER NOT NULL,
                exit_code INTEGER NOT NULL,
                stdout TEXT DEFAULT '',
                stderr TEXT DEFAULT '',
                stdout_truncated INTEGER DEFAULT 0,
                stderr_truncated INTEGER DEFAULT 0,
                failure_class TEXT NOT NULL,
                worker_id TEXT NOT NULL,
                created_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS rewards (
                reward_id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                candidate_sha256 TEXT NOT NULL,
                reward REAL,
                is_scorable INTEGER NOT NULL,
                unscorable_reason TEXT,
                scoring_version TEXT NOT NULL,
                created_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS audit_events (
                event_id TEXT PRIMARY KEY,
                actor TEXT NOT NULL,
                action TEXT NOT NULL,
                resource_id TEXT NOT NULL,
                decision TEXT NOT NULL,
                timestamp_utc TEXT NOT NULL,
                details_json TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_jobs_state ON execution_jobs(state);
            CREATE INDEX IF NOT EXISTS idx_executions_job ON executions(job_id);
            CREATE INDEX IF NOT EXISTS idx_rewards_job ON rewards(job_id);
            """)

    def create_job(self, job_id: str, task_id: str) -> None:
        """Creates a new job in PENDING state."""
        now = time.time()
        with self._lock, self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO execution_jobs (job_id, task_id, state, retry_count, created_at, updated_at)
                VALUES (?, ?, 'PENDING', 0, ?, ?)
                """,
                (job_id, task_id, now, now),
            )

    def claim_next_job(self, worker_id: str, lease_duration_seconds: float = 30.0) -> dict[str, Any] | None:
        """Claims the oldest pending or expired-lease job atomically."""
        now = time.time()
        expires_at = now + lease_duration_seconds

        with self._lock, self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT job_id, task_id, retry_count FROM execution_jobs
                WHERE state = 'PENDING' OR (state = 'RUNNING' AND lease_expires_at < ?)
                ORDER BY created_at ASC
                LIMIT 1
                """,
                (now,),
            )
            row = cursor.fetchone()
            if not row:
                return None

            job_id = row["job_id"]
            retries = row["retry_count"] + (1 if row["retry_count"] is not None else 0)

            conn.execute(
                """
                UPDATE execution_jobs
                SET state = 'RUNNING', lease_owner = ?, lease_expires_at = ?, retry_count = ?, updated_at = ?
                WHERE job_id = ?
                """,
                (worker_id, expires_at, retries, now, job_id),
            )
            return {"job_id": job_id, "task_id": row["task_id"], "retry_count": retries}

    def renew_lease(self, job_id: str, worker_id: str, extension_seconds: float = 30.0) -> bool:
        """Renews active lease if worker still holds it."""
        now = time.time()
        new_expires = now + extension_seconds
        with self._lock, self._get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE execution_jobs
                SET lease_expires_at = ?, updated_at = ?
                WHERE job_id = ? AND lease_owner = ? AND state = 'RUNNING'
                """,
                (new_expires, now, job_id, worker_id),
            )
            return cursor.rowcount > 0

    def complete_job(self, job_id: str, state: str = "COMPLETED") -> None:
        """Marks a job terminal state."""
        now = time.time()
        with self._lock, self._get_connection() as conn:
            conn.execute(
                """
                UPDATE execution_jobs
                SET state = ?, lease_owner = NULL, lease_expires_at = NULL, updated_at = ?
                WHERE job_id = ?
                """,
                (state, now, job_id),
            )

    def record_candidate(
        self,
        candidate_sha256: str,
        task_id: str,
        prompt: str,
        code: str,
        model_name: str,
        syntax_valid: bool,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
    ) -> None:
        now = time.time()
        with self._lock, self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO candidates
                (candidate_sha256, task_id, prompt, code, model_name, syntax_valid, prompt_tokens, completion_tokens, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    candidate_sha256,
                    task_id,
                    prompt,
                    code,
                    model_name,
                    1 if syntax_valid else 0,
                    prompt_tokens,
                    completion_tokens,
                    now,
                ),
            )

    def record_execution(self, exec_res: ExecutionResult) -> None:
        now = time.time()
        exec_id = f"exec-{exec_res.job_id}-{int(now * 1000)}"
        with self._lock, self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO executions (
                    execution_id, job_id, candidate_sha256, test_bundle_sha256, status,
                    passed, total, elapsed_ms, exit_code, stdout, stderr,
                    stdout_truncated, stderr_truncated, failure_class, worker_id, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    exec_id,
                    exec_res.job_id,
                    exec_res.candidate_sha256,
                    exec_res.test_bundle_sha256,
                    exec_res.status.value,
                    exec_res.passed,
                    exec_res.total,
                    exec_res.elapsed_ms,
                    exec_res.exit_code,
                    exec_res.stdout,
                    exec_res.stderr,
                    1 if exec_res.stdout_truncated else 0,
                    1 if exec_res.stderr_truncated else 0,
                    exec_res.failure_class.value,
                    exec_res.worker_id,
                    now,
                ),
            )

    def record_reward(self, reward_res: RewardResult) -> None:
        now = time.time()
        rew_id = f"rew-{reward_res.job_id}-{int(now * 1000)}"
        with self._lock, self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO rewards (
                    reward_id, job_id, candidate_sha256, reward, is_scorable,
                    unscorable_reason, scoring_version, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rew_id,
                    reward_res.job_id,
                    reward_res.candidate_sha256,
                    reward_res.reward,
                    1 if reward_res.is_scorable else 0,
                    reward_res.unscorable_reason,
                    reward_res.scoring_version,
                    now,
                ),
            )

    def record_audit(self, event: AuditEvent) -> None:
        with self._lock, self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO audit_events (
                    event_id, actor, action, resource_id, decision, timestamp_utc, details_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.actor,
                    event.action,
                    event.resource_id,
                    event.decision,
                    event.timestamp_utc,
                    json.dumps(event.details),
                ),
            )

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        """Retrieves full job details including execution and reward."""
        with self._lock, self._get_connection() as conn:
            job_row = conn.execute(
                "SELECT * FROM execution_jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
            if not job_row:
                return None

            job_dict = dict(job_row)
            exec_row = conn.execute(
                "SELECT * FROM executions WHERE job_id = ? ORDER BY created_at DESC LIMIT 1",
                (job_id,),
            ).fetchone()
            job_dict["execution"] = dict(exec_row) if exec_row else None

            reward_row = conn.execute(
                "SELECT * FROM rewards WHERE job_id = ? ORDER BY created_at DESC LIMIT 1",
                (job_id,),
            ).fetchone()
            job_dict["reward"] = dict(reward_row) if reward_row else None

            return job_dict

    def list_jobs(self, limit: int = 50, state: str | None = None) -> list[dict[str, Any]]:
        with self._lock, self._get_connection() as conn:
            if state:
                cursor = conn.execute(
                    "SELECT * FROM execution_jobs WHERE state = ? ORDER BY created_at DESC LIMIT ?",
                    (state, limit),
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM execution_jobs ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                )
            return [dict(r) for r in cursor.fetchall()]

    def list_audit_events(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM audit_events ORDER BY timestamp_utc DESC LIMIT ?",
                (limit,),
            )
            events = []
            for r in cursor.fetchall():
                d = dict(r)
                d["details"] = json.loads(d["details_json"])
                events.append(d)
            return events

    def get_summary_metrics(self) -> dict[str, Any]:
        """Calculates global platform metrics across all scored jobs."""
        with self._lock, self._get_connection() as conn:
            total_jobs = conn.execute("SELECT COUNT(*) FROM execution_jobs").fetchone()[0]
            completed_jobs = conn.execute(
                "SELECT COUNT(*) FROM execution_jobs WHERE state = 'COMPLETED'"
            ).fetchone()[0]
            failed_jobs = conn.execute(
                "SELECT COUNT(*) FROM execution_jobs WHERE state = 'FAILED'"
            ).fetchone()[0]

            reward_stats = conn.execute(
                "SELECT AVG(reward), COUNT(*) FROM rewards WHERE is_scorable = 1"
            ).fetchone()
            avg_reward = reward_stats[0] if reward_stats[0] is not None else 0.0
            scorable_count = reward_stats[1]

            infra_errors = conn.execute(
                "SELECT COUNT(*) FROM executions WHERE status = 'infra_error'"
            ).fetchone()[0]

            return {
                "total_jobs": total_jobs,
                "completed_jobs": completed_jobs,
                "failed_jobs": failed_jobs,
                "scorable_runs": scorable_count,
                "mean_reward": round(avg_reward, 4),
                "infra_errors_count": infra_errors,
            }
