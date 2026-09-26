"""MCP client helpers for personal agents (FEAT-013 / IWO-027 / IWO-029).

Deny-by-default. Repo allowlist (`platform/mcp/allowlist.json`) plus operator
connections in `~/.ai-lab/mcp-servers.json` (never Git).

Stdio transport is live (IWO-029). SSE/HTTP remain unsupported.
Agent tool names: ``mcp/<server_id>/<tool_name>``.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from .mcp import McpDenied, load_allowlist
from .mcp_stdio import (
    McpTransportError,
    StdioMcpSession,
    build_command,
    observation_from_tool_result,
)

_SAFE_ID = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
_MCP_TOOL_RE = re.compile(r"^mcp/([a-z][a-z0-9_-]{0,63})/(.+)$")


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


_ORIGINS = {"lab", "third-party", "draft"}
_NETWORKS = {"none", "loopback", "tailnet-client", "public-https"}
_NETWORK_ERROR = "network_policy must be none, loopback, tailnet-client, or public-https"
_PERMISSIONS = {"read", "privileged", "network"}
_BLOCKED_COMMAND_MARKERS = ("docker.sock", "\n", "\r")


def lab_mcp_candidate() -> dict[str, Any]:
    """Built-in lab server. Stdio process on the host, not a container."""
    script = Path(__file__).resolve().parents[3] / "scripts" / "lab-mcp-server.sh"
    return {
        "id": "ai-lab",
        "origin": "lab",
        "label": "AI Lab control plane",
        "transport": "stdio",
        "command": str(script),
        "args": [],
        "network_policy": "tailnet-client",
        "credential_ref": "lab api token",
        "capabilities": [
            {"name": "lab_health", "permission_class": "read"},
            {"name": "lab_memory_search", "permission_class": "read"},
            {"name": "lab_memory_upsert", "permission_class": "privileged"},
            {"name": "lab_scheduler_status", "permission_class": "read"},
        ],
        "runs_in": "stdio-process",
        "listed": False,
        "enabled": False,
    }


def virustotal_mcp_candidate() -> dict[str, Any]:
    """Stdio VirusTotal client. Catalog only. Not installed or listed."""
    read_tools = ("get_file_report", "get_domain_report", "get_ip_report")
    return {
        "id": "virustotal",
        "origin": "third-party",
        "label": "VirusTotal reports",
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@burtthecoder/mcp-virustotal"],
        "network_policy": "public-https",
        "credential_ref": "virustotal api key",
        "capabilities": [
            {"name": name, "permission_class": "read"} for name in read_tools
        ] + [
            {"name": "get_url_report", "permission_class": "privileged"},
            {"name": "search_vt", "permission_class": "privileged"},
        ],
        "first_binding": list(read_tools),
        "omitted_from_first_binding": ["get_url_report", "search_vt"],
        "runs_in": "stdio-process",
        "listed": False,
        "enabled": False,
    }


def cve_lookup_mcp_candidate() -> dict[str, Any]:
    """Keyless NVD, OSV, and CISA KEV lookups from cve-mcp. Other package tools are not declared."""
    read_tools = ("nvd_get", "nvd_search", "kev_check", "osv_query", "osv_get")
    return {
        "id": "cve-lookup",
        "origin": "third-party",
        "label": "CVE lookup (NVD, OSV, CISA KEV)",
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "cve-mcp"],
        "network_policy": "public-https",
        "credential_ref": "",
        "capabilities": [{"name": name, "permission_class": "read"} for name in read_tools],
        "first_binding": list(read_tools),
        "omitted_from_first_binding": [
            "exploit_search",
            "shodan_ip_vulns",
            "nuclei_check",
            "msf_check",
        ],
        "runs_in": "stdio-process",
        "listed": False,
        "enabled": False,
        "package_note": "cve-mcp exposes more tools. Only the names in capabilities can be bound.",
    }


def intake_candidates() -> list[dict[str, Any]]:
    return [lab_mcp_candidate(), virustotal_mcp_candidate(), cve_lookup_mcp_candidate()]


def _clean_capabilities(raw: Any) -> list[dict[str, str]]:
    if not isinstance(raw, list):
        raise ValueError("capabilities must be a list")
    out: list[dict[str, str]] = []
    for item in raw:
        if isinstance(item, str):
            name, klass = item, "read"
        elif isinstance(item, dict):
            name = str(item.get("name") or "")
            klass = str(item.get("permission_class") or "read")
        else:
            raise ValueError("each capability needs a name")
        if not re.match(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$", name):
            raise ValueError("invalid capability name")
        if klass not in _PERMISSIONS:
            raise ValueError("permission_class must be read, privileged, or network")
        out.append({"name": name, "permission_class": klass})
    return out


def _clean_bindings(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    out = []
    for item in raw:
        if not isinstance(item, dict) or not item.get("agent_id"):
            continue
        caps = [str(name) for name in (item.get("capabilities") or [])]
        out.append({"agent_id": str(item["agent_id"]), "capabilities": caps})
    return out


def _public_server(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(item["id"]),
        "label": str(item.get("label") or item["id"]),
        "origin": str(item.get("origin") or "third-party"),
        "transport": str(item.get("transport") or "stdio"),
        "command": str(item.get("command") or ""),
        "args": list(item.get("args") or []),
        "enabled": bool(item.get("enabled", False)),
        "listed": bool(item.get("listed", False)),
        "network_policy": str(item.get("network_policy") or "none"),
        "credential_ref": str(item.get("credential_ref") or ""),
        "capabilities": _clean_capabilities(item.get("capabilities") or []),
        "bindings": _clean_bindings(item.get("bindings") or []),
        "runs_in": "stdio-process",
        "source": "local",
    }


def local_servers() -> list[dict[str, Any]]:
    out = []
    for item in _read_local().get("servers") or []:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        try:
            out.append(_public_server(item))
        except ValueError:
            continue
    return out


def listed_server_ids() -> frozenset[str]:
    """Repo allowlist plus local servers an operator has explicitly listed."""
    local_ids = {s["id"] for s in local_servers() if s.get("listed")}
    return frozenset(repo_listed_ids() | local_ids)


def assert_allowed(server_id: str) -> None:
    if server_id not in listed_server_ids():
        raise McpDenied(
            f"MCP server {server_id!r} is not allowlisted. "
            "Add it under Settings → MCP servers (local) or platform/mcp/allowlist.json."
        )


def get_local_server(server_id: str) -> dict[str, Any] | None:
    for s in local_servers():
        if s["id"] == server_id:
            return s
    return None


def _reject_command(command: str, args: list[str]) -> None:
    blob = " ".join([command, *args])
    for marker in _BLOCKED_COMMAND_MARKERS:
        if marker in blob:
            raise ValueError("command is not allowed")
    if not command.strip():
        raise ValueError("command is required")


def _validate_credential_ref(value: str) -> str:
    ref = value.strip()
    if not ref:
        return ""
    if len(ref) > 80 or "=" in ref or ref.lower().startswith("sk-"):
        raise ValueError("credential_ref must be a name, not a secret")
    return ref


def submit_mcp_intake(
    *,
    server_id: str,
    origin: str,
    label: str = "",
    command: str = "",
    args: list[str] | None = None,
    network_policy: str = "none",
    credential_ref: str = "",
    capabilities: list[Any] | None = None,
) -> dict[str, Any]:
    """Record a lab, third-party, or draft server. It stays unlisted."""
    if origin not in _ORIGINS:
        raise ValueError("origin must be lab, third-party, or draft")
    if network_policy not in _NETWORKS:
        raise ValueError(_NETWORK_ERROR)
    if origin == "lab":
        if server_id != "ai-lab":
            raise ValueError("the lab origin is only the ai-lab server")
        candidate = lab_mcp_candidate()
        command = str(candidate["command"])
        args = list(candidate["args"])
        capabilities = list(candidate["capabilities"])
        network_policy = str(candidate["network_policy"])
        credential_ref = str(candidate["credential_ref"])
        label = label or str(candidate["label"])
    else:
        if not capabilities:
            raise ValueError("capabilities are required")
        _reject_command(command, list(args or []))
    return upsert_local_server(
        server_id=server_id,
        label=label,
        transport="stdio",
        command=command,
        args=list(args or []),
        enabled=False,
        listed=False,
        origin=origin,
        network_policy=network_policy,
        credential_ref=_validate_credential_ref(credential_ref),
        capabilities=_clean_capabilities(capabilities or []),
    )


def authorize_mcp_server(server_id: str) -> dict[str, Any]:
    """Operator listing step. A saved intake stays denied until this runs."""
    current = get_local_server(server_id)
    if current is None:
        raise McpDenied(f"MCP server {server_id!r} has no intake record")
    if current.get("transport") != "stdio":
        raise ValueError("only stdio servers can be listed")
    if not current.get("command"):
        raise ValueError("command is required")
    if not current.get("capabilities"):
        raise ValueError("capabilities are required before listing")
    return upsert_local_server(
        server_id=server_id,
        label=str(current.get("label") or server_id),
        transport="stdio",
        command=str(current.get("command") or ""),
        args=list(current.get("args") or []),
        enabled=True,
        listed=True,
        origin=str(current.get("origin") or "third-party"),
        network_policy=str(current.get("network_policy") or "none"),
        credential_ref=str(current.get("credential_ref") or ""),
        capabilities=list(current.get("capabilities") or []),
        bindings=list(current.get("bindings") or []),
    )


def bind_mcp_agent(server_id: str, agent_id: str, capabilities: list[str]) -> dict[str, Any]:
    """Name which declared tools one agent may call. Does not list the server."""
    if not agent_id or not _SAFE_ID.match(agent_id):
        raise ValueError("invalid agent id")
    current = get_local_server(server_id)
    if current is None:
        raise McpDenied(f"MCP server {server_id!r} has no intake record")
    declared = {item["name"] for item in current.get("capabilities") or []}
    requested = tuple(capabilities)
    if not requested or not set(requested) <= declared:
        raise ValueError("binding capabilities must be declared on the server")
    bindings = [b for b in current.get("bindings") or [] if b.get("agent_id") != agent_id]
    bindings.append({"agent_id": agent_id, "capabilities": list(requested)})
    return upsert_local_server(
        server_id=server_id,
        label=str(current.get("label") or server_id),
        transport=str(current.get("transport") or "stdio"),
        command=str(current.get("command") or ""),
        args=list(current.get("args") or []),
        enabled=bool(current.get("enabled")),
        listed=bool(current.get("listed")),
        origin=str(current.get("origin") or "third-party"),
        network_policy=str(current.get("network_policy") or "none"),
        credential_ref=str(current.get("credential_ref") or ""),
        capabilities=list(current.get("capabilities") or []),
        bindings=bindings,
    )


def binding_allows(server_id: str, agent_id: str, tool_name: str) -> bool:
    server = get_local_server(server_id)
    if server is None:
        return False
    for binding in server.get("bindings") or []:
        if binding.get("agent_id") == agent_id and tool_name in (binding.get("capabilities") or []):
            return True
    return False


def capability_needs_approval(server_id: str, tool_name: str) -> bool:
    server = get_local_server(server_id)
    if server is None:
        return True
    for item in server.get("capabilities") or []:
        if item.get("name") == tool_name:
            return item.get("permission_class") in {"privileged", "network"}
    return bool(server.get("capabilities"))


def upsert_local_server(
    *,
    server_id: str,
    label: str = "",
    transport: str = "stdio",
    command: str = "",
    args: list[str] | None = None,
    enabled: bool = False,
    listed: bool | None = None,
    origin: str = "third-party",
    network_policy: str = "none",
    credential_ref: str = "",
    capabilities: list[Any] | None = None,
    bindings: list[Any] | None = None,
) -> dict[str, Any]:
    if not _SAFE_ID.match(server_id):
        raise ValueError("invalid server id")
    if transport not in {"stdio", "sse", "http"}:
        raise ValueError("transport must be stdio|sse|http")
    if origin not in _ORIGINS:
        raise ValueError("origin must be lab, third-party, or draft")
    if network_policy not in _NETWORKS:
        raise ValueError(_NETWORK_ERROR)
    data = _read_local()
    servers = [s for s in (data.get("servers") or []) if isinstance(s, dict)]
    previous = next((s for s in servers if s.get("id") == server_id), {})
    entry = {
        "id": server_id,
        "label": (label or server_id).strip(),
        "origin": origin,
        "transport": transport,
        "command": command.strip(),
        "args": list(args or []),
        "enabled": enabled,
        "listed": bool(previous.get("listed", False)) if listed is None else listed,
        "network_policy": network_policy,
        "credential_ref": _validate_credential_ref(credential_ref) if credential_ref else str(previous.get("credential_ref") or ""),
        "capabilities": _clean_capabilities(capabilities if capabilities is not None else previous.get("capabilities") or []),
        "bindings": _clean_bindings(bindings if bindings is not None else previous.get("bindings") or []),
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
    saved = _public_server(entry)
    return saved


def delete_local_server(server_id: str) -> bool:
    data = _read_local()
    before = len(data.get("servers") or [])
    data["servers"] = [
        s for s in (data.get("servers") or []) if not (isinstance(s, dict) and s.get("id") == server_id)
    ]
    _write_local(data)
    return len(data["servers"]) < before


def mcp_tool_name(server_id: str, tool_name: str) -> str:
    return f"mcp/{server_id}/{tool_name}"


def parse_mcp_tool_name(name: str) -> tuple[str, str] | None:
    m = _MCP_TOOL_RE.match(name or "")
    if not m:
        return None
    return m.group(1), m.group(2)


def mcp_client_status() -> dict[str, Any]:
    data = load_allowlist()
    local = local_servers()
    stdio_ready = any(s.get("enabled") and s.get("transport") == "stdio" and s.get("command") for s in local)
    return {
        "ok": True,
        "policy": data.get("policy"),
        "listed_servers": sorted(listed_server_ids()),
        "repo_servers": sorted(repo_listed_ids()),
        "local_servers": local,
        "transport": "stdio" if stdio_ready else "stdio-ready",
        "note": (
            "Stdio MCP is live (IWO-029). Connections in ~/.ai-lab/mcp-servers.json. "
            "SSE/HTTP transports are not implemented. Agent tools use mcp/<server>/<tool>."
        ),
    }


def list_mcp_tools(server_id: str) -> list[dict[str, Any]]:
    assert_allowed(server_id)
    server = get_local_server(server_id)
    if server is None:
        raise McpDenied(
            f"MCP server {server_id!r} is repo-allowlisted only; "
            "add a local stdio command under Settings to call it."
        )
    if not server.get("enabled"):
        raise McpDenied(f"MCP server {server_id!r} is disabled")
    if server.get("transport") != "stdio":
        raise McpTransportError(
            f"transport {server.get('transport')!r} not implemented (stdio only in IWO-029)"
        )
    argv = build_command(str(server.get("command") or ""), list(server.get("args") or []))
    with StdioMcpSession(argv) as session:
        tools = session.list_tools()
    out = []
    for t in tools:
        name = str(t.get("name") or "")
        out.append(
            {
                "name": name,
                "agent_tool": mcp_tool_name(server_id, name),
                "description": str(t.get("description") or ""),
                "input_schema": t.get("inputSchema") or t.get("input_schema") or {},
            }
        )
    return out


def bound_agent_tool_names(agent_id: str, server_ids: list[str]) -> list[str]:
    """Tool names this agent is bound to. Does not start a server process."""
    names: list[str] = []
    for server_id in server_ids:
        server = get_local_server(server_id)
        if server is None or not server.get("listed"):
            continue
        for binding in server.get("bindings") or []:
            if binding.get("agent_id") != agent_id:
                continue
            for cap in binding.get("capabilities") or []:
                names.append(mcp_tool_name(server_id, str(cap)))
    return names


def list_mcp_agent_tools(server_ids: list[str]) -> list[str]:
    """Discover agent-facing tool names for the given servers (best-effort)."""
    names: list[str] = []
    for sid in server_ids:
        try:
            for t in list_mcp_tools(sid):
                if t.get("agent_tool"):
                    names.append(str(t["agent_tool"]))
        except (McpDenied, McpTransportError, ValueError, OSError):
            continue
    return names


def call_mcp_tool(
    server_id: str,
    tool_name: str,
    arguments: dict[str, Any] | None = None,
) -> dict[str, Any]:
    assert_allowed(server_id)
    server = get_local_server(server_id)
    if server is None:
        raise McpDenied(
            f"MCP server {server_id!r} is repo-allowlisted only; "
            "add a local stdio command under Settings to call it."
        )
    if not server.get("enabled"):
        return {
            "ok": False,
            "denied": True,
            "server_id": server_id,
            "tool": tool_name,
            "args": arguments or {},
            "observation": f"MCP server {server_id!r} is disabled",
        }
    declared = [item["name"] for item in server.get("capabilities") or []]
    if declared and tool_name not in declared:
        return {
            "ok": False,
            "denied": True,
            "server_id": server_id,
            "tool": tool_name,
            "args": arguments or {},
            "observation": f"MCP tool {tool_name!r} is not declared on {server_id!r}",
        }
    if server.get("transport") != "stdio":
        return {
            "ok": False,
            "denied": False,
            "server_id": server_id,
            "tool": tool_name,
            "args": arguments or {},
            "observation": (
                f"MCP transport {server.get('transport')!r} not implemented "
                "(stdio only in IWO-029)."
            ),
        }
    try:
        argv = build_command(str(server.get("command") or ""), list(server.get("args") or []))
        with StdioMcpSession(argv) as session:
            result = session.call_tool(tool_name, arguments or {})
        obs = observation_from_tool_result(result)
        ok = not bool(result.get("isError"))
        return {
            "ok": ok,
            "denied": False,
            "server_id": server_id,
            "tool": tool_name,
            "args": arguments or {},
            "observation": obs[:8000],
            "raw": result,
        }
    except McpTransportError as exc:
        return {
            "ok": False,
            "denied": False,
            "server_id": server_id,
            "tool": tool_name,
            "args": arguments or {},
            "observation": f"MCP transport error: {exc}",
        }


def require_mcp_servers(server_ids: list[str]) -> None:
    for sid in server_ids:
        assert_allowed(sid)


__all__ = [
    "McpDenied",
    "McpTransportError",
    "assert_allowed",
    "authorize_mcp_server",
    "bind_mcp_agent",
    "binding_allows",
    "bound_agent_tool_names",
    "call_mcp_tool",
    "capability_needs_approval",
    "delete_local_server",
    "lab_mcp_candidate",
    "submit_mcp_intake",
    "get_local_server",
    "list_mcp_agent_tools",
    "list_mcp_tools",
    "listed_server_ids",
    "local_servers",
    "mcp_client_status",
    "mcp_tool_name",
    "parse_mcp_tool_name",
    "require_mcp_servers",
    "upsert_local_server",
]
