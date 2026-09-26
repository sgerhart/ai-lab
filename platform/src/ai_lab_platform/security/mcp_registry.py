"""Governed MCP registry. Discovery is not authorization (IWO-067)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..mcp import McpDenied, load_allowlist
from .events import SecurityEvent
from .store import EventLog, MemoryEventLog

# Metadata for the lab's own MCP server. It stays unauthorized until an allowlist row exists.
LAB_MCP_CATALOG: dict[str, dict[str, Any]] = {
    "ai-lab": {
        "title": "AI Lab control-plane MCP",
        "transport": "stdio",
        "capabilities": (
            {"name": "lab_health", "permission_class": "read"},
            {"name": "lab_memory_search", "permission_class": "read"},
            {"name": "lab_memory_upsert", "permission_class": "privileged"},
            {"name": "lab_scheduler_status", "permission_class": "read"},
        ),
        "credential_ref": "lab api token",
        "network_policy": "tailnet-client",
    }
}


@dataclass(frozen=True)
class UseDecision:
    allowed: bool
    reason: str


class McpRegistry:
    def __init__(
        self,
        *,
        allowlist_path: Path | None = None,
        events: EventLog | None = None,
    ) -> None:
        self.allowlist_path = allowlist_path
        self.events = events or MemoryEventLog()
        self._bindings: dict[tuple[str, str], tuple[str, ...]] = {}

    def authorized_servers(self) -> list[dict[str, Any]]:
        data = load_allowlist(self.allowlist_path)
        if data.get("policy") != "deny-unlisted":
            raise ValueError("MCP allowlist policy must be deny-unlisted")
        rows = []
        for item in data.get("servers") or []:
            if not isinstance(item, dict) or not item.get("id"):
                raise ValueError("each MCP server needs an id")
            rows.append(self._record(str(item["id"]), item, listed=True))
        return rows

    def catalog(self) -> list[dict[str, Any]]:
        listed = {row["id"] for row in self.authorized_servers()}
        rows = []
        for server_id, meta in LAB_MCP_CATALOG.items():
            record = self._record(server_id, meta, listed=server_id in listed)
            record["authorized"] = server_id in listed
            rows.append(record)
        return rows

    def bindings(self) -> list[dict[str, Any]]:
        return [
            {"agent_id": agent_id, "server_id": server_id, "capabilities": list(caps)}
            for (agent_id, server_id), caps in sorted(self._bindings.items())
        ]

    def view(self) -> dict[str, Any]:
        return {
            "policy": "deny-unlisted",
            "servers": self.authorized_servers(),
            "catalog": self.catalog(),
            "bindings": self.bindings(),
        }

    def bind(self, agent_id: str, server_id: str, capabilities: list[str]) -> SecurityEvent:
        if not agent_id:
            raise ValueError("agent_id is required")
        allowed = {row["id"]: row for row in self.authorized_servers()}
        if server_id not in allowed:
            event = self._decision_event(
                agent_id=agent_id,
                server_id=server_id,
                capability="",
                allowed=False,
                reason="unlisted",
                summary="MCP binding denied",
            )
            self.events.append(event)
            raise McpDenied(f"MCP server {server_id!r} is not allowlisted")
        known = {item["name"] for item in allowed[server_id]["capabilities"]}
        requested = tuple(capabilities)
        if not requested or not set(requested) <= known:
            event = self._decision_event(
                agent_id=agent_id,
                server_id=server_id,
                capability=",".join(requested),
                allowed=False,
                reason="capability not declared",
                summary="MCP binding denied",
            )
            self.events.append(event)
            raise McpDenied(f"MCP capability is not declared on {server_id!r}")
        self._bindings[(agent_id, server_id)] = requested
        event = self._decision_event(
            agent_id=agent_id,
            server_id=server_id,
            capability=",".join(requested),
            allowed=True,
            reason="binding recorded",
            summary="MCP binding allowed",
        )
        self.events.append(event)
        return event

    def decide(
        self,
        *,
        agent_id: str,
        server_id: str,
        capability: str,
        run_id: str = "",
        job_id: str = "",
    ) -> tuple[UseDecision, SecurityEvent]:
        allowed = {row["id"] for row in self.authorized_servers()}
        bound = self._bindings.get((agent_id, server_id), ())
        if server_id not in allowed:
            decision = UseDecision(False, "unlisted")
        elif capability not in bound:
            decision = UseDecision(False, "not bound")
        else:
            decision = UseDecision(True, "bound capability")
        event = self._decision_event(
            agent_id=agent_id,
            server_id=server_id,
            capability=capability,
            allowed=decision.allowed,
            reason=decision.reason,
            summary="MCP use allowed" if decision.allowed else "MCP use denied",
            run_id=run_id,
            job_id=job_id,
        )
        self.events.append(event)
        return decision, event

    def _record(self, server_id: str, item: dict[str, Any], *, listed: bool) -> dict[str, Any]:
        catalog = LAB_MCP_CATALOG.get(server_id, {})
        capabilities = item.get("capabilities") or catalog.get("capabilities") or ()
        normalized = []
        for cap in capabilities:
            if isinstance(cap, dict) and cap.get("name"):
                normalized.append(
                    {
                        "name": str(cap["name"]),
                        "permission_class": str(cap.get("permission_class") or "read"),
                    }
                )
            elif isinstance(cap, str):
                normalized.append({"name": cap, "permission_class": "read"})
        return {
            "id": server_id,
            "title": str(item.get("title") or item.get("purpose") or catalog.get("title") or server_id),
            "transport": str(item.get("transport") or catalog.get("transport") or "stdio"),
            "capabilities": normalized,
            "credential_ref": str(item.get("credential_ref") or catalog.get("credential_ref") or ""),
            "network_policy": str(item.get("network") or item.get("network_policy") or catalog.get("network_policy") or "none"),
            "listed": listed,
        }

    def _decision_event(
        self,
        *,
        agent_id: str,
        server_id: str,
        capability: str,
        allowed: bool,
        reason: str,
        summary: str,
        run_id: str = "",
        job_id: str = "",
    ) -> SecurityEvent:
        return SecurityEvent.create(
            provider="mcp",
            severity="info" if allowed else "low",
            classification="mcp",
            summary=summary,
            agent_id=agent_id,
            resource_id=server_id,
            run_id=run_id,
            job_id=job_id,
            tool=capability,
            details={"decision": "allow" if allowed else "deny", "reason": reason},
        )
