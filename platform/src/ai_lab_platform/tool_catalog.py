"""Tools and MCP servers the builder can hand to an agent.

Native names here are ones the mini loop can run. MCP rows come from the
intake catalog. Registering one records it and leaves it off.
"""

from __future__ import annotations

import re
from typing import Any

from .mcp_client import intake_candidates

# Implemented reads. Privileged and disabled tools are not granted by a build.
READ_TOOLS = frozenset(
    {
        "health_read",
        "compose_ps_read",
        "repo_read",
        "repo_search",
        "git_status",
        "git_diff",
        "memory_search",
        "vault_list",
        "vault_grep",
        "vault_read",
        "web_search",
        "files_list",
        "files_grep",
        "files_read",
        "research",
        "report_list",
        "report_read",
        "report_write",
        "write_report_artifact",
    }
)

_REPO = ("repo", "codebase", "patch", "git diff", "git status", "source file")
_HEALTH = ("service health", "lab health", "compose status", "health_read")
_CVE = re.compile(r"\b(cve|nvd|osv|kev|vulnerability|vulnerabilities)\b", re.IGNORECASE)
_VT = re.compile(r"\b(virustotal|virus total|file reputation)\b", re.IGNORECASE)


def extra_read_tools(names: list[str] | None) -> list[str]:
    """Keep only reads the loop can execute. Drop edits, deploys, and unknown names."""
    out: list[str] = []
    for name in names or []:
        if name in READ_TOOLS and name not in out:
            out.append(name)
    return out


def _read_binding(candidate: dict[str, Any]) -> list[str]:
    bound = candidate.get("first_binding")
    if isinstance(bound, list) and bound:
        return [str(name) for name in bound]
    names: list[str] = []
    for item in candidate.get("capabilities") or []:
        if isinstance(item, dict) and item.get("permission_class") == "read" and item.get("name"):
            names.append(str(item["name"]))
    return names


def catalog_servers() -> list[dict[str, Any]]:
    """Sanitized catalog cards. No command, args, or secret."""
    cards: list[dict[str, Any]] = []
    for item in intake_candidates():
        sid = str(item.get("id") or "")
        if not sid:
            continue
        tools = _read_binding(item)
        cards.append(
            {
                "id": f"mcp:{sid}",
                "server_id": sid,
                "name": str(item.get("label") or sid),
                "origin": "catalog_mcp",
                "publisher": str(item.get("origin") or "third-party"),
                "transport": str(item.get("transport") or ""),
                "execution_host": "mac-mini" if item.get("transport") == "stdio" else "remote",
                "connection_state": "off",
                "last_checked_at": None,
                "tools": [{"name": name, "description": "Catalog read tool. Not callable until authorized.", "risk": "read"} for name in tools],
                "permitted": False,
                "used": False,
                "risk": "read",
            }
        )
    return cards


def access_for(text: str, purpose: str, *, shape: str = "agent") -> dict[str, Any]:
    """Native reads and catalog servers a finished build should record."""
    blob = text or ""
    lower = blob.lower()
    native: list[str] = []
    servers: list[str] = []
    mcp_tools: list[str] = []
    skills: list[str] = []

    if any(word in lower for word in _REPO) or purpose == "build":
        native.extend(["repo_read", "repo_search", "git_status", "git_diff"])
    if any(word in lower for word in _HEALTH) or (purpose == "lab" and "health" in lower):
        native.extend(["health_read", "compose_ps_read"])
    if shape != "workflow" and purpose in {"learn", "product", "company", "lab"}:
        native.append("memory_search")
    if shape != "workflow" and purpose == "personal":
        native.extend(
            ["vault_list", "vault_grep", "vault_read", "files_list", "files_grep", "files_read", "web_search", "research", "report_list", "report_read", "report_write"]
        )
    if shape != "workflow" and purpose in {"learn", "product", "company"} and any(
        word in lower for word in ("note", "report", "write", "summary", "summarize")
    ):
        native.append("write_report_artifact")

    by_id = {str(item["id"]): item for item in intake_candidates()}
    if _CVE.search(blob):
        servers.append("cve-lookup")
        skills.append("Look up a CVE")
    if _VT.search(blob):
        servers.append("virustotal")
        skills.append("Read a file report")
    for sid in servers:
        item = by_id.get(sid) or {}
        for name in _read_binding(item):
            if name not in mcp_tools:
                mcp_tools.append(name)

    if shape == "workflow":
        native = [name for name in native if name in {"health_read", "compose_ps_read", "repo_read", "repo_search", "git_status", "git_diff"}]

    return {
        "tools": extra_read_tools(native),
        "mcp_offers": servers,
        "mcp_tools": mcp_tools,
        "skills": skills,
    }
