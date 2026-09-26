"""Policy evaluation that hands off to the existing approval gate."""

from __future__ import annotations

from ..approvals import requires_approval


def evaluate_tool(
    *,
    tool: str,
    allowed_tools: list[str],
    already_approved: set[str],
) -> dict[str, object]:
    """Return the same allow/deny result as ``approvals.requires_approval``.

    This function does not grant tools and does not skip a privileged gate.
    """
    needs = requires_approval(tool, list(allowed_tools), set(already_approved))
    return {
        "tool": tool,
        "allowed": not needs,
        "needs_approval": bool(needs),
        "authority": "approvals.requires_approval",
    }
