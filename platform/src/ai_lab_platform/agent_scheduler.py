"""Fire due personal-agent schedules (FEAT-009 / IWO-030).

State lives under ``~/.ai-lab/schedule-state.json`` (never Git).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .agent_definitions import AgentDefinition, AgentDefinitionStore
from .schedule_cron import CronError, cron_matches
from .work_order import utcnow


def schedule_state_path() -> Path:
    return Path.home() / ".ai-lab" / "schedule-state.json"


def _read_state(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"last_fired": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"last_fired": {}}
    if not isinstance(data.get("last_fired"), dict):
        data["last_fired"] = {}
    return data


def _write_state(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    path.chmod(0o600)


def minute_key(when: datetime) -> str:
    local = when.astimezone()
    return local.strftime("%Y-%m-%dT%H:%M")


Runner = Callable[[AgentDefinition], dict[str, Any]]


def tick(
    store: AgentDefinitionStore,
    *,
    run_definition: Runner,
    now: datetime | None = None,
    state_path: Path | None = None,
) -> dict[str, Any]:
    """Evaluate schedules; start at most one run per definition per local minute."""
    when = now or datetime.now().astimezone()
    path = state_path or schedule_state_path()
    state = _read_state(path)
    last_fired: dict[str, str] = dict(state.get("last_fired") or {})
    key = minute_key(when)

    started: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for definition in store.list():
        cron = (definition.schedule_cron or "").strip()
        if not cron:
            continue
        try:
            due = cron_matches(cron, when)
        except CronError as exc:
            errors.append(
                {
                    "definition_id": definition.id,
                    "title": definition.title,
                    "error": f"invalid_cron: {exc}",
                }
            )
            continue
        if not due:
            skipped.append(
                {
                    "definition_id": definition.id,
                    "title": definition.title,
                    "reason": "not_due",
                }
            )
            continue
        prev = last_fired.get(definition.id, "")
        if prev == key:
            skipped.append(
                {
                    "definition_id": definition.id,
                    "title": definition.title,
                    "reason": "already_fired_this_minute",
                }
            )
            continue
        try:
            result = run_definition(definition)
        except Exception as exc:  # noqa: BLE001 — surface per-definition failure
            errors.append(
                {
                    "definition_id": definition.id,
                    "title": definition.title,
                    "error": str(exc),
                }
            )
            continue
        last_fired[definition.id] = key
        started.append(
            {
                "definition_id": definition.id,
                "title": definition.title,
                "run_id": result.get("id"),
                "status": result.get("status"),
                "fired_at": utcnow(),
            }
        )

    state["last_fired"] = last_fired
    state["last_tick_at"] = datetime.now(timezone.utc).isoformat()
    _write_state(path, state)

    return {
        "ok": True,
        "when": when.isoformat(),
        "minute_key": key,
        "started": started,
        "skipped": skipped,
        "errors": errors,
    }


def status(*, state_path: Path | None = None) -> dict[str, Any]:
    path = state_path or schedule_state_path()
    state = _read_state(path)
    return {
        "ok": True,
        "state_path": str(path),
        "last_tick_at": state.get("last_tick_at"),
        "last_fired": state.get("last_fired") or {},
    }


__all__ = ["minute_key", "schedule_state_path", "status", "tick"]
