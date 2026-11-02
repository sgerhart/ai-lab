"""Agent security posture evaluator (FEAT-018 / IWO-068).

Renders effective security posture from existing agent policy, tool
privilege gates, and MCP registry governance. Does not create a parallel
permission system. UI labels must distinguish intent from enforced policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..approvals import PRIVILEGED_TOOLS, is_privileged
from ..policy import AgentPolicy, load_policy
from .mcp_registry import McpRegistry

PERMANENTLY_DENIED_TOOLS = frozenset(
    {
        "git_push",
        "gh_pr_merge",
        "deploy",
        "brew_apply",
        "compose_up",
        "compose_down_volumes",
        "restore_live",
        "rotate_credentials",
        "firewall_change",
        "ssh_config_write",
        "host_mutate",
        "rm_rf",
        "secrets_read",
        "hypervisor_admin",
        "network_bridge_mutate",
        "trusted_network_attach",
        "raw_shell_exec",
        "template_mutate",
    }
)


@dataclass(frozen=True)
class AgentSecurityPosture:
    agent_id: str
    title: str
    isolation_tier: int
    read_only: bool
    filesystem_class: str
    network_class: str
    network_endpoints: tuple[str, ...]
    secret_access: str
    allowed_tools: tuple[str, ...]
    privileged_tools: tuple[str, ...]
    approval_required_tools: tuple[str, ...]
    denied_tools: tuple[str, ...]
    mcp_servers: list[dict[str, Any]]
    audit_logging: bool
    warnings: list[str]
    intent_vs_policy: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "title": self.title,
            "isolation_tier": self.isolation_tier,
            "read_only": self.read_only,
            "filesystem_class": self.filesystem_class,
            "network_class": self.network_class,
            "network_endpoints": list(self.network_endpoints),
            "secret_access": self.secret_access,
            "allowed_tools": list(self.allowed_tools),
            "privileged_tools": list(self.privileged_tools),
            "approval_required_tools": list(self.approval_required_tools),
            "denied_tools": list(self.denied_tools),
            "mcp_servers": list(self.mcp_servers),
            "audit_logging": self.audit_logging,
            "warnings": list(self.warnings),
            "intent_vs_policy": dict(self.intent_vs_policy),
        }


def evaluate_agent_posture(
    agent_id: str,
    *,
    title: str = "",
    requested_tools: list[str] | None = None,
    mcp_server_ids: list[str] | None = None,
    agents_root: Path | None = None,
    mcp_registry: McpRegistry | None = None,
) -> AgentSecurityPosture:
    """Evaluate effective security posture of an agent definition or draft."""
    try:
        policy = load_policy(agent_id, agents_root=agents_root)
    except (FileNotFoundError, ValueError):
        policy = AgentPolicy(
            id=agent_id,
            allowed_tools=(),
            privileged_tools=(),
            read_only=True,
            isolation_tier=1,
            network=(),
            citation_policy=None,
        )

    req_tools = list(requested_tools or [])
    mcp_ids = list(mcp_server_ids or [])
    warnings: list[str] = []

    # 1. Isolation tier
    isolation_tier = policy.isolation_tier
    if agent_id == "coding-assistant":
        isolation_tier = 2 if any(t in req_tools for t in ("apply_patch", "git_commit", "sandbox")) else 1
    elif agent_id == "security":
        isolation_tier = 2

    # 2. Filesystem class
    if agent_id == "coding-assistant":
        filesystem_class = "isolated-worktree"
    elif agent_id == "personal":
        filesystem_class = "user-vault-scoped"
    elif agent_id == "research":
        filesystem_class = "reports-scoped"
    elif agent_id == "security":
        filesystem_class = "isolated-vm"
    elif policy.read_only and not any(is_privileged(t) for t in req_tools):
        filesystem_class = "read-only"
    else:
        filesystem_class = "bounded-local"

    # 3. Network class
    if agent_id == "security":
        network_class = "isolated-bridge"
        endpoints = ()
    elif any(t in req_tools for t in ("web_search", "research", "web")) or "allowlist" in policy.network or agent_id in ("research", "personal"):
        network_class = "egress-allowlist"
        endpoints = ("https://*",)
    elif "tailscale-health" in policy.network or "tailnet" in policy.network:
        network_class = "tailnet-client"
        endpoints = policy.network
    elif "loopback" in policy.network:
        network_class = "loopback-only"
        endpoints = ("127.0.0.1:8001",)
    elif len(policy.network) == 0:
        network_class = "none"
        endpoints = ()
    else:
        network_class = "tailnet-client"
        endpoints = policy.network

    # 4. Secret access
    secret_access = "none"
    if "consult_frontier" in req_tools or "deep_research" in req_tools:
        secret_access = "gated-vault"

    # 5. Tool partitioning
    enforced_allowed: list[str] = []
    enforced_approval: list[str] = []
    unsupported_tools: list[str] = []

    for t in req_tools:
        if t in PERMANENTLY_DENIED_TOOLS:
            warnings.append(f"Tool '{t}' is permanently denied for automated agents.")
            continue
        policy_allowed = set(policy.allowed_tools)
        policy_privileged = set(policy.privileged_tools)
        if t in policy_allowed:
            enforced_allowed.append(t)
        elif t in policy_privileged or is_privileged(t):
            enforced_approval.append(t)
        else:
            if t in ("files", "git", "memory", "web", "reports"):
                enforced_allowed.append(t)
            elif t == "sandbox":
                enforced_approval.append("apply_patch")
            else:
                unsupported_tools.append(t)
                warnings.append(f"Tool '{t}' is not permitted under policy for '{agent_id}'.")

    for pt in policy.privileged_tools:
        if pt not in enforced_approval and pt not in PERMANENTLY_DENIED_TOOLS:
            enforced_approval.append(pt)

    # 6. MCP governance
    mcp_posture: list[dict[str, Any]] = []
    if mcp_registry:
        try:
            authorized = {s["id"]: s for s in mcp_registry.authorized_servers()}
        except Exception:
            authorized = {}
        for sid in mcp_ids:
            if sid in authorized:
                mcp_posture.append({"id": sid, "status": "authorized", "policy": "governed"})
            else:
                mcp_posture.append({"id": sid, "status": "unlisted_denied", "policy": "deny-unlisted"})
                warnings.append(f"MCP server '{sid}' is unlisted and denied under default security policy.")
    elif mcp_ids:
        for sid in mcp_ids:
            mcp_posture.append({"id": sid, "status": "unverified", "policy": "deny-unlisted"})

    intent_vs_policy = {
        "requested_tools": req_tools,
        "enforced_allowed": enforced_allowed,
        "enforced_approval_required": enforced_approval,
        "unsupported_tools": unsupported_tools,
        "status": "aligned" if not unsupported_tools else "constrained_by_policy",
        "policy_authority": f"agents/{agent_id}/policy.json",
    }

    return AgentSecurityPosture(
        agent_id=agent_id,
        title=title or agent_id,
        isolation_tier=isolation_tier,
        read_only=policy.read_only,
        filesystem_class=filesystem_class,
        network_class=network_class,
        network_endpoints=endpoints,
        secret_access=secret_access,
        allowed_tools=policy.allowed_tools,
        privileged_tools=policy.privileged_tools,
        approval_required_tools=tuple(sorted(set(enforced_approval))),
        denied_tools=tuple(sorted(PERMANENTLY_DENIED_TOOLS)),
        mcp_servers=mcp_posture,
        audit_logging=True,
        warnings=warnings,
        intent_vs_policy=intent_vs_policy,
    )
