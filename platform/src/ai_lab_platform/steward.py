"""Standing goals for the personal agent (FEAT-022 / IWO-107).

Goal records live under ``~/.ai-lab/steward/goals.json`` (never Git).
A background wake may use the See class only. This module does not call a model.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from .agent_scheduler import minute_key
from .conversation import AgentRun, AgentRunStatus, BillingClass, Conversation, RunBudget
from .policy import AgentPolicy, load_policy
from .schedule_cron import CronError, cron_matches, parse_cron

_ACTIVITY_CAP = 100
_WAKE_STEPS = 4
_NOTE_CAP = 500

SEE_TOOLS = frozenset(
    {
        "files_grep",
        "files_list",
        "files_read",
        "health_read",
        "nexus_search",
        "presentation_list",
        "presentation_read",
        "report_list",
        "report_read",
        "schedule_list",
        "skill_list",
        "skill_read",
        "vault_grep",
        "vault_list",
        "vault_read",
        "web_search",
    }
)
DRAFT_TOOLS = frozenset(
    {
        "presentation_write",
        "report_write",
        "research",
        "skill_create",
        "vault_write",
    }
)
APPROVAL_TOOLS = frozenset(
    {
        "consult_frontier",
        "schedule_cancel",
        "schedule_create",
    }
)

_MAX_TITLE = 200
_MAX_INTENT = 4000
_MAX_TOOLS = 32


class StewardError(ValueError):
    """A goal or the goals file cannot be used."""


def default_goals_path() -> Path:
    return Path.home() / ".ai-lab" / "steward" / "goals.json"


def classify_tool(name: str) -> str:
    if name in SEE_TOOLS:
        return "see"
    if name in DRAFT_TOOLS:
        return "draft"
    if name in APPROVAL_TOOLS:
        return "approval"
    if name.startswith("mcp/"):
        try:
            from .mcp_client import capability_needs_approval, parse_mcp_tool_name

            parsed = parse_mcp_tool_name(name)
            if parsed:
                sid, tname = parsed
                return "approval" if capability_needs_approval(sid, tname) else "see"
        except Exception:
            pass
    return "never"


def access_manifest(policy: AgentPolicy | None = None) -> dict[str, list[str]]:
    """Classify the personal policy and bound MCP tools. Tools outside the three classes are never."""
    loaded = policy or load_policy("personal")
    classes: dict[str, list[str]] = {"see": [], "draft": [], "approval": [], "never": []}
    for name in tuple(loaded.allowed_tools) + tuple(loaded.privileged_tools):
        classes[classify_tool(name)].append(name)
    try:
        from .mcp_client import bound_agent_tool_names, local_servers

        sids = [s["id"] for s in local_servers() if s.get("listed")]
        for mcp_tool in bound_agent_tool_names("personal", sids):
            c = classify_tool(mcp_tool)
            if mcp_tool not in classes[c]:
                classes[c].append(mcp_tool)
    except Exception:
        pass
    return classes


def background_tools(goal: dict[str, Any], *, policy: AgentPolicy | None = None) -> list[str]:
    """See tools named on the goal. Draft, approval, and never are absent."""
    see = set(access_manifest(policy)["see"])
    named = goal.get("see_tools")
    if not isinstance(named, list):
        return []
    return [name for name in named if isinstance(name, str) and name in see]


def _public(goal: dict[str, Any]) -> dict[str, Any]:
    see = goal.get("see_tools")
    names = [name for name in see if isinstance(name, str)] if isinstance(see, list) else []
    mcps = goal.get("mcp_server_ids")
    mcp_list = [str(x) for x in mcps if isinstance(x, str)] if isinstance(mcps, list) else []
    return {
        "id": str(goal.get("id") or ""),
        "title": str(goal.get("title") or ""),
        "intent": str(goal.get("intent") or ""),
        "status": str(goal.get("status") or ""),
        "wake_cron": str(goal.get("wake_cron") or ""),
        "see_tools": names,
        "mcp_server_ids": mcp_list,
        "last_due_at": goal.get("last_due_at"),
    }


def _read(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"goals": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StewardError("goals file is not valid json") from exc
    if not isinstance(data, dict) or not isinstance(data.get("goals"), list):
        raise StewardError("goals file is not a goal list")
    return data


def _write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.parent.chmod(0o700)
    text = json.dumps(data, indent=2, sort_keys=True) + "\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.chmod(0o600)
    temporary.replace(path)
    path.chmod(0o600)


def list_goals(*, path: Path | None = None) -> list[dict[str, Any]]:
    data = _read(path or default_goals_path())
    goals = [item for item in data["goals"] if isinstance(item, dict) and item.get("id")]
    return [_public(item) for item in goals]


def _clean_text(value: str, *, limit: int, field: str) -> str:
    text = value.strip()
    if "\x00" in text:
        raise StewardError(f"{field} contains a null")
    if len(text) > limit:
        raise StewardError(f"{field} is longer than {limit} characters")
    return text


def create_goal(
    *,
    title: str,
    intent: str,
    wake_cron: str,
    see_tools: list[str] | None = None,
    path: Path | None = None,
    policy: AgentPolicy | None = None,
) -> dict[str, Any]:
    cleaned_title = _clean_text(title, limit=_MAX_TITLE, field="title")
    if not cleaned_title:
        raise StewardError("title is required")
    cleaned_intent = _clean_text(intent, limit=_MAX_INTENT, field="intent")
    cron = wake_cron.strip()
    try:
        parse_cron(cron)
    except CronError as exc:
        raise StewardError(f"invalid wake_cron: {exc}") from exc

    manifest = access_manifest(policy)
    see = manifest["see"]
    if see_tools is None:
        chosen = list(see)
    else:
        if len(see_tools) > _MAX_TOOLS:
            raise StewardError(f"see_tools is longer than {_MAX_TOOLS}")
        refused = [name for name in see_tools if name not in see]
        if refused:
            raise StewardError(
                "background goals may only use see tools; refused: " + ", ".join(refused)
            )
        chosen = []
        for name in see_tools:
            if name not in chosen:
                chosen.append(name)
    if not chosen:
        raise StewardError("a goal needs at least one see tool")

    mcp_sids: list[str] = []
    try:
        from .mcp_client import parse_mcp_tool_name

        for t in chosen:
            parsed = parse_mcp_tool_name(t)
            if parsed and parsed[0] not in mcp_sids:
                mcp_sids.append(parsed[0])
    except Exception:
        pass

    goal = {
        "id": uuid.uuid4().hex,
        "title": cleaned_title,
        "intent": cleaned_intent,
        "status": "active",
        "wake_cron": cron,
        "see_tools": chosen,
        "mcp_server_ids": mcp_sids,
        "last_due_at": None,
        "last_due_minute": "",
    }
    store_path = path or default_goals_path()
    data = _read(store_path)
    data["goals"].append(goal)
    _write(store_path, data)
    return _public(goal)


def _require_id(goal_id: str) -> str:
    if len(goal_id) != 32 or any(ch not in "0123456789abcdef" for ch in goal_id):
        raise StewardError("unknown goal")
    return goal_id


def _mutate(goal_id: str, status: str, *, path: Path | None = None) -> dict[str, Any]:
    cleaned = _require_id(goal_id)
    store_path = path or default_goals_path()
    data = _read(store_path)
    for item in data["goals"]:
        if isinstance(item, dict) and item.get("id") == cleaned:
            if item.get("status") == "done" and status != "done":
                raise StewardError("a closed goal stays closed")
            item["status"] = status
            _write(store_path, data)
            return _public(item)
    raise StewardError("unknown goal")


def pause_goal(goal_id: str, *, path: Path | None = None) -> dict[str, Any]:
    return _mutate(goal_id, "paused", path=path)


def resume_goal(goal_id: str, *, path: Path | None = None) -> dict[str, Any]:
    return _mutate(goal_id, "active", path=path)


def close_goal(goal_id: str, *, path: Path | None = None) -> dict[str, Any]:
    return _mutate(goal_id, "done", path=path)


def get_goal(goal_id: str, *, path: Path | None = None) -> dict[str, Any]:
    cleaned = _require_id(goal_id)
    store_path = path or default_goals_path()
    data = _read(store_path)
    for item in data["goals"]:
        if isinstance(item, dict) and item.get("id") == cleaned:
            return dict(item)
    raise StewardError("unknown goal")


def activity_path_for(goals_path: Path) -> Path:
    return goals_path.with_name("activity.json")


def _read_activity(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"entries": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StewardError("activity file is not valid json") from exc
    if not isinstance(data, dict) or not isinstance(data.get("entries"), list):
        raise StewardError("activity file is not an entry list")
    return data


def _public_activity(entry: dict[str, Any]) -> dict[str, Any]:
    tools = entry.get("see_tools")
    names = [name for name in tools if isinstance(name, str)] if isinstance(tools, list) else []
    return {
        "id": str(entry.get("id") or ""),
        "goal_id": str(entry.get("goal_id") or ""),
        "goal_title": str(entry.get("goal_title") or ""),
        "at": entry.get("at"),
        "run_id": entry.get("run_id"),
        "status": str(entry.get("status") or ""),
        "see_tools": names,
        "note": str(entry.get("note") or ""),
    }


def list_activity(*, path: Path | None = None) -> list[dict[str, Any]]:
    goals_path = path or default_goals_path()
    data = _read_activity(activity_path_for(goals_path))
    entries = [item for item in data["entries"] if isinstance(item, dict)]
    return [_public_activity(item) for item in reversed(entries)]


def _append_activity(entry: dict[str, Any], *, path: Path) -> dict[str, Any]:
    act_path = activity_path_for(path)
    data = _read_activity(act_path)
    data["entries"].append(entry)
    data["entries"] = data["entries"][-_ACTIVITY_CAP:]
    _write(act_path, data)
    return _public_activity(entry)


def enqueue_wake(
    goal: dict[str, Any],
    *,
    store: Any,
    path: Path,
    model: str,
    backend: str,
) -> dict[str, Any]:
    """Queue one read-only personal run. Does not call a model."""
    tools = background_tools(goal)
    now = datetime.now().astimezone().isoformat()
    if not tools:
        return _append_activity(
            {
                "id": uuid.uuid4().hex,
                "goal_id": str(goal.get("id") or ""),
                "goal_title": str(goal.get("title") or ""),
                "at": now,
                "run_id": None,
                "status": "skipped",
                "see_tools": [],
                "note": "no see tools",
            },
            path=path,
        )
    title = str(goal.get("title") or "goal").strip()[:80]
    intent = str(goal.get("intent") or "").strip()[:_MAX_INTENT]
    conversation = Conversation.new(agent="personal", title=f"Steward: {title}")
    store.put_conversation(conversation)
    objective = (
        f"Standing goal: {title}\n{intent}\n"
        "Look only with the read tools you were given. "
        "Leave a short note of what you found and what needs the operator."
    )
    run = AgentRun.new(
        agent="personal",
        objective=objective[:4000],
        conversation_id=conversation.id,
        model=model,
        billing_class=BillingClass.LOCAL,
        backend=backend,
        budget=RunBudget(max_steps=_WAKE_STEPS, max_time_seconds=120),
    )
    run.tool_ceiling = list(tools)
    run.steward_goal_id = str(goal.get("id") or "")
    mcp_sids = goal.get("mcp_server_ids")
    if not isinstance(mcp_sids, list):
        mcp_sids = []
        try:
            from .mcp_client import parse_mcp_tool_name

            for t in tools:
                parsed = parse_mcp_tool_name(t)
                if parsed and parsed[0] not in mcp_sids:
                    mcp_sids.append(parsed[0])
        except Exception:
            pass
    run.mcp_server_ids = list(mcp_sids)
    run.status = AgentRunStatus.QUEUED
    store.put_agent_run(run)
    return _append_activity(
        {
            "id": uuid.uuid4().hex,
            "goal_id": run.steward_goal_id,
            "goal_title": title,
            "at": now,
            "run_id": run.id,
            "status": "queued",
            "see_tools": list(tools),
            "note": "",
        },
        path=path,
    )


def wake_due(
    when: datetime,
    *,
    store: Any,
    path: Path | None = None,
    model: str,
    backend: str,
) -> list[dict[str, Any]]:
    """Mark due goals and enqueue one read-only run for each newly marked goal."""
    store_path = path or default_goals_path()
    marked = mark_due(when, path=store_path)
    woken: list[dict[str, Any]] = []
    for goal in marked:
        item = dict(goal)
        try:
            entry = enqueue_wake(
                goal,
                store=store,
                path=store_path,
                model=model,
                backend=backend,
            )
        except Exception as exc:  # noqa: BLE001 — one goal must not drop the tick
            entry = _append_activity(
                {
                    "id": uuid.uuid4().hex,
                    "goal_id": str(goal.get("id") or ""),
                    "goal_title": str(goal.get("title") or ""),
                    "at": datetime.now().astimezone().isoformat(),
                    "run_id": None,
                    "status": "error",
                    "see_tools": [],
                    "note": str(exc)[:300],
                },
                path=store_path,
            )
        item["run_id"] = entry.get("run_id")
        item["activity_status"] = entry.get("status")
        woken.append(item)
    return woken


def note_wake_finished(run: AgentRun, *, path: Path | None = None) -> dict[str, Any] | None:
    """Record the finished wake on the activity entry for this run."""
    if not (run.steward_goal_id or "").strip() or not run.id:
        return None
    goals_path = path or default_goals_path()
    act_path = activity_path_for(goals_path)
    if not act_path.is_file():
        return None
    data = _read_activity(act_path)
    status = run.status.value if isinstance(run.status, AgentRunStatus) else str(run.status)
    note = (run.final_result or run.error or "")[:_NOTE_CAP]
    for entry in data["entries"]:
        if isinstance(entry, dict) and entry.get("run_id") == run.id:
            entry["status"] = status
            entry["note"] = note
            _write(act_path, data)
            return _public_activity(entry)
    return None


def mark_due(when: datetime, *, path: Path | None = None) -> list[dict[str, Any]]:
    """Mark active goals whose cron matches ``when``. One mark per local minute.

    Does not call a model and does not insert an agent run.
    """
    store_path = path or default_goals_path()
    if not store_path.is_file():
        return []
    data = _read(store_path)
    key = minute_key(when)
    marked: list[dict[str, Any]] = []
    changed = False
    for item in data["goals"]:
        if not isinstance(item, dict):
            continue
        if item.get("status") != "active":
            continue
        cron = str(item.get("wake_cron") or "").strip()
        if not cron:
            continue
        try:
            due = cron_matches(cron, when)
        except CronError:
            continue
        if not due or item.get("last_due_minute") == key:
            continue
        item["last_due_minute"] = key
        item["last_due_at"] = when.isoformat()
        changed = True
        marked.append(_public(item))
    if changed:
        _write(store_path, data)
    return marked


__all__ = [
    "APPROVAL_TOOLS",
    "DRAFT_TOOLS",
    "SEE_TOOLS",
    "StewardError",
    "access_manifest",
    "background_tools",
    "classify_tool",
    "close_goal",
    "create_goal",
    "default_goals_path",
    "enqueue_wake",
    "get_goal",
    "list_activity",
    "list_goals",
    "mark_due",
    "note_wake_finished",
    "pause_goal",
    "resume_goal",
    "wake_due",
]
