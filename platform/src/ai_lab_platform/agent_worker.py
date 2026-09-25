"""Drain queued agent runs in the background (FEAT-002 / IWO-031).

One run at a time. State of truth remains Postgres/SQLite agent_runs rows.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from .agent_loop import run_until_idle
from .conversation import AgentRun, AgentRunStatus
from .model_router import ModelRouter
from .tools import ToolContext

_lock = threading.Lock()


def list_queued_runs(store: Any) -> list[AgentRun]:
    if not hasattr(store, "list_agent_runs"):
        return []
    runs = store.list_agent_runs(None)
    return [r for r in runs if r.status == AgentRunStatus.QUEUED]


def drain_queued_runs(
    store: Any,
    router: ModelRouter,
    *,
    limit: int = 1,
) -> dict[str, Any]:
    """Claim up to ``limit`` queued runs and execute until idle."""
    processed: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    if limit < 1:
        return {"ok": True, "processed": processed, "errors": errors, "queued_remaining": 0}

    with _lock:
        queued = list_queued_runs(store)
        batch = queued[:limit]
        for run in batch:
            try:
                # Re-read to avoid racing a cancel
                current = store.get_agent_run(run.id)
                if current is None or current.status != AgentRunStatus.QUEUED:
                    continue
                ctx = None
                if (current.workspace_root or "").strip():
                    root = Path(current.workspace_root)
                    ctx = ToolContext(workspace_root=root, artifact_root=root / "artifacts")
                finished = run_until_idle(
                    current,
                    router=router,
                    store_put=store.put_agent_run,
                    ctx=ctx,
                )
                processed.append(
                    {
                        "id": finished.id,
                        "status": finished.status.value,
                        "error": finished.error,
                    }
                )
            except Exception as exc:  # noqa: BLE001 — per-run isolation
                errors.append({"id": run.id, "error": str(exc)})
                try:
                    failed = store.get_agent_run(run.id)
                    if failed is not None and failed.status == AgentRunStatus.QUEUED:
                        failed.status = AgentRunStatus.FAILED
                        failed.error = f"worker_error:{exc}"
                        store.put_agent_run(failed)
                except Exception:  # noqa: BLE001
                    pass

    remaining = len(list_queued_runs(store))
    return {
        "ok": True,
        "processed": processed,
        "errors": errors,
        "queued_remaining": remaining,
    }


class AgentRunWorker:
    """Daemon thread that periodically drains the queue."""

    def __init__(
        self,
        store: Any,
        router: ModelRouter,
        *,
        interval_sec: float = 2.0,
    ) -> None:
        self._store = store
        self._router = router
        self._interval = max(0.5, float(interval_sec))
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._loop,
            name="ai-lab-agent-run-worker",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=self._interval + 1.0)

    def _loop(self) -> None:
        while not self._stop.wait(self._interval):
            try:
                drain_queued_runs(self._store, self._router, limit=1)
            except Exception:  # noqa: BLE001 — never kill the thread
                continue


__all__ = ["AgentRunWorker", "drain_queued_runs", "list_queued_runs"]
