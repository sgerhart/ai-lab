"""MCP client helpers for personal agents (FEAT-013 / IWO-027).

Deny-by-default. Repo allowlist (`platform/mcp/allowlist.json`) plus operator
connections in `~/.ai-lab/mcp-servers.json` (never Git). Live transport is still
a stub — connecting here registers identity for agents to reference.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from .mcp import McpDenied, load_allowlist

_SAFE_ID = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")


def local_servers_path() -> Path:
    override = os.environ.get("AI_LAB_MCP_SERVERS")
    if override:
        return Path(override)
    return Path.home() / ".ai-lab" / "mcp-servers.json"


def _read_local() -> dict[str, Any]:
    path = local_servers_path()
    if not path.is_file():
        return {"servers": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data.get("servers"), list):
        return {"servers": []}
    return data


def _write_local(data: dict[str, Any]) -> None:
    path = local_servers_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.chmod(path, 0o600)


def repo_listed_ids() -> frozenset[str]:
    data = load_allowlist()
    ids = []
    for item in data.get("servers") or []:
        if isinstance(item, dict) and item.get("id"):
            ids.append(str(item["id"]))
    return frozenset(ids)


def local_servers() -> list[dict[str, Any]]:
    out = []
    for item in _read_local().get("servers") or []:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        out.append(
            {
                "id": str(item["id"]),
                "label": str(item.get("label") or item["id"]),
                "transport": str(item.get("transport") or "stdio"),
                "command": str(item.get("command") or ""),
                "args": list(item.get("args") or []),
                "enabled": bool(item.get("enabled", True)),
                "source": "local",
            }
        )
    return out


def listed_server_ids() -> frozenset[str]:
    local_ids = {s["id"] for s in local_servers() if s.get("enabled")}
    return frozenset(repo_listed_ids() | local_ids)


def assert_allowed(server_id: str) -> None:
    if server_id not in listed_server_ids():
        raise McpDenied(
            f"MCP server {server_id!r} is not allowlisted. "
            "Add it under Settings → MCP servers (local) or platform/mcp/allowlist.json."
        )


def upsert_local_server(
    *,
    server_id: str,
    label: str = "",
    transport: str = "stdio",
    command: str = "",
    args: list[str] | None = None,
    enabled: bool = True,
) -> dict[str, Any]:
    if not _SAFE_ID.match(server_id):
        raise ValueError("invalid server id")
    if transport not in {"stdio", "sse", "http"}:
        raise ValueError("transport must be stdio|sse|http")
    data = _read_local()
    servers = [s for s in (data.get("servers") or []) if isinstance(s, dict)]
    entry = {
        "id": server_id,
        "label": (label or server_id).strip(),
        "transport": transport,
        "command": command.strip(),
        "args": list(args or []),
        "enabled": enabled,
    }
    replaced = False
    for i, s in enumerate(servers):
        if s.get("id") == server_id:
            servers[i] = entry
            replaced = True
            break
    if not replaced:
        servers.append(entry)
    data["servers"] = servers
    _write_local(data)
    return {**entry, "source": "local"}


def delete_local_server(server_id: str) -> bool:
    data = _read_local()
    before = len(data.get("servers") or [])
    data["servers"] = [
        s for s in (data.get("servers") or []) if not (isinstance(s, dict) and s.get("id") == server_id)
    ]
    _write_local(data)
    return len(data["servers"]) < before


def mcp_client_status() -> dict[str, Any]:
    data = load_allowlist()
    local = local_servers()
    return {
        "ok": True,
        "policy": data.get("policy"),
        "listed_servers": sorted(listed_server_ids()),
        "repo_servers": sorted(repo_listed_ids()),
        "local_servers": local,
        "transport": "stub",
        "note": (
            "Connections saved under ~/.ai-lab/mcp-servers.json. "
            "Live MCP tool calls are stubbed until transport is wired."
        ),
    }


def call_mcp_tool(
    server_id: str,
    tool_name: str,
    arguments: dict[str, Any] | None = None,
) -> dict[str, Any]:
    assert_allowed(server_id)
    return {
        "ok": False,
        "denied": False,
        "server_id": server_id,
        "tool": tool_name,
        "args": arguments or {},
        "observation": (
            f"MCP server {server_id!r} is registered but client transport is not "
            "implemented yet (IWO-027 stub)."
        ),
    }


def require_mcp_servers(server_ids: list[str]) -> None:
    for sid in server_ids:
        assert_allowed(sid)


__all__ = [
    "McpDenied",
    "assert_allowed",
    "call_mcp_tool",
    "delete_local_server",
    "listed_server_ids",
    "local_servers",
    "mcp_client_status",
    "require_mcp_servers",
    "upsert_local_server",
]
