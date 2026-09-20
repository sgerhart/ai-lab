"""Privileged-tool gate. Human approval is required before these tools run."""

from __future__ import annotations

PRIVILEGED_TOOLS = frozenset(
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
    }
)


def is_privileged(tool: str) -> bool:
    return tool in PRIVILEGED_TOOLS


def requires_approval(tool: str, allowed_tools: list[str], already_approved: set[str]) -> bool:
    if tool not in allowed_tools:
        return True
    if is_privileged(tool) and tool not in already_approved:
        return True
    return False
