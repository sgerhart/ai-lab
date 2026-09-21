"""MCP server allowlist. Unlisted servers are denied. None are enabled yet."""

from __future__ import annotations

import json
from pathlib import Path


class McpDenied(PermissionError):
    pass


def allowlist_path() -> Path:
    return Path(__file__).resolve().parents[3] / "platform" / "mcp" / "allowlist.json"


def load_allowlist(path: Path | None = None) -> dict:
    data = json.loads((path or allowlist_path()).read_text(encoding="utf-8"))
    if data.get("policy") != "deny-unlisted":
        raise ValueError("MCP allowlist policy must be deny-unlisted")
    servers = data.get("servers")
    if not isinstance(servers, list):
        raise ValueError("MCP allowlist.servers must be a list")
    return data


def listed_server_ids(path: Path | None = None) -> frozenset[str]:
    data = load_allowlist(path)
    ids = []
    for item in data.get("servers") or []:
        if not isinstance(item, dict) or not item.get("id"):
            raise ValueError("each MCP server needs an id")
        ids.append(str(item["id"]))
    return frozenset(ids)


def assert_allowed(server_id: str, path: Path | None = None) -> None:
    allowed = listed_server_ids(path)
    if server_id not in allowed:
        raise McpDenied(
            f"MCP server {server_id!r} is not allowlisted. "
            "Add an ADR and platform/mcp/allowlist.json entry before enabling it."
        )
