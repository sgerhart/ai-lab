"""Sanitized capability catalog for the chat-first Studio header.

A configured MCP server is not "connected" and is not an approval to call its tools.
This module does not spawn MCP processes or perform handshakes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .mcp_client import local_servers, repo_listed_ids
from .policy import load_policy

_TOOL_BLURB = {
    "health_read": "Read loopback health for lab services on the mini.",
    "compose_ps_read": "Read compose service status.",
    "repo_read": "Read a file inside the authorized workspace.",
    "repo_search": "Search the authorized workspace.",
    "git_status": "Show git status for the workspace.",
    "git_diff": "Show a truncated git diff.",
    "memory_search": "Search lab memory.",
    "apply_patch": "Apply a patch. Requires approval and an isolated copy.",
    "git_commit": "Commit in an isolated copy. Requires approval.",
}


def assistant_name(agent_id: str) -> str:
    if agent_id == "lab-operations":
        return "AI Lab Assistant"
    return agent_id


def _built_in(name: str, *, state: str, permitted: bool, risk: str, checked: str) -> dict[str, Any]:
    return {
        "id": f"built_in:{name}",
        "name": name,
        "origin": "built_in",
        "publisher": "ai-lab",
        "transport": "in-process",
        "execution_host": "mac-mini",
        "connection_state": state,
        "last_checked_at": checked,
        "tools": [{"name": name, "description": _TOOL_BLURB.get(name, ""), "risk": risk}],
        "permitted": permitted,
        "used": False,
        "risk": risk,
    }


def _mcp_state(server: dict[str, Any]) -> str:
    if not server.get("enabled", True):
        return "disabled"
    transport = str(server.get("transport") or "")
    if transport != "stdio" or not str(server.get("command") or "").strip():
        return "unavailable"
    return "configured"


def _mcp_cap(server: dict[str, Any]) -> dict[str, Any]:
    sid = str(server.get("id") or "")
    return {
        "id": f"mcp:{sid}",
        "name": str(server.get("label") or sid),
        "origin": "custom_mcp",
        "publisher": "operator",
        "transport": str(server.get("transport") or ""),
        "execution_host": "mac-mini",
        "connection_state": _mcp_state(server),
        "last_checked_at": None,
        "tools": [],
        "permitted": False,
        "used": False,
        "risk": "unknown",
    }


def capability_catalog(agent_id: str = "lab-operations", *, now: datetime | None = None) -> dict[str, Any]:
    checked = (now or datetime.now(timezone.utc)).replace(microsecond=0).isoformat()
    try:
        policy = load_policy(agent_id)
    except (FileNotFoundError, ValueError) as exc:
        return {
            "ok": False,
            "agent": agent_id,
            "assistant_name": assistant_name(agent_id),
            "restart_recovery": "not_yet_verified",
            "error": str(exc),
            "capabilities": [],
        }

    caps: list[dict[str, Any]] = []
    for name in policy.allowed_tools:
        caps.append(_built_in(name, state="connected", permitted=True, risk="read", checked=checked))
    for name in policy.privileged_tools:
        caps.append(
            _built_in(
                name,
                state="permission_required",
                permitted=False,
                risk="privileged",
                checked=checked,
            )
        )

    seen: set[str] = set()
    for server in local_servers():
        if not isinstance(server, dict):
            continue
        sid = str(server.get("id") or "")
        if not sid:
            continue
        seen.add(sid)
        caps.append(_mcp_cap(server))
    for sid in sorted(repo_listed_ids()):
        if sid in seen:
            continue
        caps.append(
            _mcp_cap(
                {
                    "id": sid,
                    "label": sid,
                    "enabled": True,
                    "transport": "",
                    "command": "",
                }
            )
        )

    return {
        "ok": True,
        "agent": policy.id,
        "assistant_name": assistant_name(policy.id),
        "restart_recovery": "not_yet_verified",
        "note": (
            "configured means saved, not connected. "
            "A connection is not permission to call tools. "
            "Restart recovery is not yet verified."
        ),
        "capabilities": caps,
    }
