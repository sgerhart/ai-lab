"""Execute allowlisted tools for the mini agent loop (IWO-005)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .approvals import is_privileged, requires_approval
from .tools import ToolContext, ToolError, compose_ps_read, git_status, health_read, repo_read


@dataclass
class ToolRequest:
    name: str
    args: dict[str, Any]
    action_id: str


@dataclass
class ToolResult:
    name: str
    ok: bool
    observation: str
    denied: bool = False


def default_workspace() -> Path:
    return Path(__file__).resolve().parents[3]


def build_tool_context(*, bounded_scope: str = "") -> ToolContext:
    root = default_workspace()
    return ToolContext(
        workspace_root=root,
        artifact_root=root / "artifacts" / "agent-runs",
        bounded_scope=bounded_scope,
    )


def _refuse_privileged(name: str) -> str:
    raise ToolError(
        f"{name} is not executed by the mini agent loop "
        "(approval may be recorded; live privileged exec needs a dedicated IWO)"
    )


_HANDLERS: dict[str, Callable[..., str]] = {
    "health_read": lambda ctx, **_a: health_read(),
    "compose_ps_read": lambda ctx, **_a: compose_ps_read(),
    "repo_read": lambda ctx, **a: repo_read(ctx, limit=int(a.get("limit", 50))),
    "git_status": lambda ctx, **_a: git_status(ctx),
    "git_push": lambda ctx, **_a: _refuse_privileged("git_push"),
    "deploy": lambda ctx, **_a: _refuse_privileged("deploy"),
    "gh_pr_merge": lambda ctx, **_a: _refuse_privileged("gh_pr_merge"),
}


def execute_allowed_tool(
    name: str,
    args: dict[str, Any],
    *,
    allowed_tools: list[str],
    approved_tools: set[str],
    ctx: ToolContext | None = None,
) -> ToolResult:
    effective_allowed = list(allowed_tools)
    if name in approved_tools and name not in effective_allowed:
        effective_allowed.append(name)
    if name not in effective_allowed:
        return ToolResult(name=name, ok=False, observation=f"tool not allowed: {name}", denied=True)
    if requires_approval(name, effective_allowed, approved_tools):
        return ToolResult(
            name=name,
            ok=False,
            observation=f"tool requires approval: {name}",
            denied=True,
        )
    if name not in _HANDLERS:
        return ToolResult(name=name, ok=False, observation=f"unknown tool: {name}", denied=True)
    ctx = ctx or build_tool_context()
    try:
        text = _HANDLERS[name](ctx, **(args or {}))
        return ToolResult(name=name, ok=True, observation=text)
    except ToolError as exc:
        return ToolResult(name=name, ok=False, observation=str(exc))


def tool_needs_human_gate(
    name: str,
    allowed_tools: list[str],
    approved_tools: set[str],
    privileged_tools: list[str] | None = None,
) -> bool:
    if name in approved_tools:
        return False
    privileged_tools = privileged_tools or []
    if is_privileged(name) or name in privileged_tools:
        return True
    if name not in allowed_tools:
        return False  # hard deny, not a human gate
    return requires_approval(name, allowed_tools, approved_tools)
