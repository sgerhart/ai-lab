"""Deterministic local plans for the three catalog agents.

Not an LLM loop. The laptop worker and the Studio worker share this module.
Privileged tools are never in the default plan and must not run without approval.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .approvals import requires_approval
from .tools import ToolContext, ToolError, compose_ps_read, git_diff, git_status, health_read, http_get_allowlist, repo_read, repo_search, write_report_artifact
from .work_order import WorkOrder


@dataclass
class PlanResult:
    ok: bool
    detail: str
    artifacts: list[str] = field(default_factory=list)
    tools_run: list[str] = field(default_factory=list)
    blocked_tool: str | None = None


def plan_for(agent: str) -> list[str]:
    if agent == "lab-operations":
        return ["health_read", "compose_ps_read"]
    if agent == "research":
        return ["write_report_artifact"]
    if agent == "development":
        return ["repo_read", "git_status"]
    if agent == "coding-assistant":
        return ["repo_read", "repo_search", "git_status", "git_diff"]
    raise ToolError(f"no local plan for agent {agent}")


def execute_plan(
    agent: str,
    objective: str,
    ctx: ToolContext,
    allowed_tools: list[str],
    approved_tools: set[str] | None = None,
) -> PlanResult:
    approved = approved_tools or set()
    try:
        plan = plan_for(agent)
    except ToolError as exc:
        return PlanResult(ok=False, detail=str(exc))

    notes: list[str] = []
    artifacts: list[str] = []
    ran: list[str] = []
    for tool in plan:
        if requires_approval(tool, allowed_tools, approved):
            return PlanResult(
                ok=False,
                detail=f"approval required: {tool}",
                artifacts=artifacts,
                tools_run=ran,
                blocked_tool=tool,
            )
        try:
            body = _execute(tool, ctx, objective, artifacts)
        except ToolError as exc:
            return PlanResult(
                ok=False,
                detail=f"{tool}: {exc}",
                artifacts=artifacts,
                tools_run=ran,
            )
        ran.append(tool)
        notes.append(f"## {tool}\n{body}")
    return PlanResult(
        ok=True,
        detail="\n\n".join(notes) if notes else "no tools ran",
        artifacts=artifacts,
        tools_run=ran,
    )


def execute_work_order(order: WorkOrder, ctx: ToolContext) -> PlanResult:
    return execute_plan(
        order.agent,
        order.objective,
        ctx,
        list(order.allowed_tools),
        set(order.approved_tools),
    )


def _execute(tool: str, ctx: ToolContext, objective: str, artifacts: list[str]) -> str:
    if tool == "health_read":
        return health_read()
    if tool == "compose_ps_read":
        return compose_ps_read()
    if tool == "repo_read":
        return repo_read(ctx)
    if tool == "repo_search":
        return repo_search(ctx, objective[:80] or "def ")
    if tool == "git_status":
        return git_status(ctx)
    if tool == "git_diff":
        return git_diff(ctx)
    if tool == "write_report_artifact":
        body = (
            f"# Research report\n\nObjective: {objective}\n\n"
            "Sources retrieved: none (http_get_allowlist disabled).\n"
            "Inference: none. Limitations: no live retrieval; citations were not invented.\n"
        )
        path = write_report_artifact(ctx, body)
        artifacts.append(path)
        return path
    if tool == "http_get_allowlist":
        return http_get_allowlist("")
    if tool in {"git_push", "gh_pr_merge", "deploy"}:
        raise ToolError(f"privileged tool {tool} is not in the local plan and will not run")
    raise ToolError(f"tool not implemented in local plan: {tool}")
