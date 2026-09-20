"""Deterministic local worker. Not an LLM loop and not deployed to the Studio."""

from __future__ import annotations

from pathlib import Path

from .agent_plans import execute_work_order
from .orchestrator import Orchestrator
from .policy import constrain_tools, load_policy
from .tools import ToolContext
from .work_order import WorkOrder


def _ctx(order: WorkOrder, workspace_root: Path, artifact_root: Path) -> ToolContext:
    return ToolContext(
        workspace_root=workspace_root,
        artifact_root=artifact_root / order.id,
        bounded_scope=order.bounded_scope,
    )


def run_order(
    orch: Orchestrator,
    order: WorkOrder,
    *,
    workspace_root: Path,
    artifact_root: Path,
    agents_root: Path | None = None,
) -> WorkOrder:
    policy = load_policy(order.agent, agents_root=agents_root)
    allowed = constrain_tools(order.allowed_tools or list(policy.allowed_tools), policy)
    order.allowed_tools = allowed
    orch.store.put(order)
    ctx = _ctx(order, workspace_root, artifact_root)
    result = execute_work_order(order, ctx)
    if result.blocked_tool:
        return orch.request_tool(order.id, result.blocked_tool, set(order.approved_tools))
    order.artifacts.extend(result.artifacts)
    orch.store.put(order)
    if not result.ok:
        return orch.fail(order.id, result.detail)
    return orch.complete(order.id, result.detail)


def tick(
    orch: Orchestrator,
    *,
    workspace_root: Path,
    artifact_root: Path,
    agents_root: Path | None = None,
) -> WorkOrder | None:
    started = orch.start_next()
    if started is None:
        return None
    return run_order(
        orch,
        started,
        workspace_root=workspace_root,
        artifact_root=artifact_root,
        agents_root=agents_root,
    )
