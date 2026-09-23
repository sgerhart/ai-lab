"""Bounded personal-agent model/tool loop on the mini (FEAT-010 / IWO-005 / IWO-020).

Runs on the control plane. FakeBackend / ScriptedToolBackend in tests; live
Studio Ollama via the same TOOL/FINAL protocol when the model cooperates.
Deterministic agent_plans.py remains a separate fixture.
"""

from __future__ import annotations

import ast
import json
import re
from typing import Any
from uuid import uuid4

from .conversation import AgentRun, AgentRunStatus
from .model_router import CompletionRequest, ModelRouter
from .policy import AgentPolicy, load_policy
from .tool_runtime import (
    ToolContext,
    build_tool_context,
    execute_allowed_tool,
    tool_needs_human_gate,
)
from .work_order import utcnow

_TOOL_RE = re.compile(r"^TOOL\s+(\S+)(?:\s+(\{.*\}))?\s*$", re.DOTALL)
_TOOL_LINE_RE = re.compile(r"(?m)^TOOL\s+(\S+)(?:\s+(\{.*\}))?\s*$")
_FINAL_RE = re.compile(r"^FINAL\s*(.*)$", re.DOTALL)
_FINAL_LINE_RE = re.compile(r"(?m)^FINAL\s*(.*)$")
_JSON_TOOL_RE = re.compile(
    r'\{\s*"type"\s*:\s*"tool"\s*,\s*"name"\s*:\s*"([^"]+)"\s*,\s*"args"\s*:\s*(\{.*?\})\s*\}',
    re.DOTALL,
)


def loop_system_prompt(policy: AgentPolicy) -> str:
    """Instruct live models (Ollama) to emit the harness TOOL/FINAL protocol."""
    allowed = ", ".join(policy.allowed_tools) or "(none)"
    privileged = ", ".join(policy.privileged_tools) or "(none)"
    return (
        f"You are the {policy.id} agent for ai-lab on the Mac mini control plane.\n"
        f"Isolation tier {policy.isolation_tier}; read_only={policy.read_only}.\n"
        f"Allowed tools (no approval): {allowed}.\n"
        f"Privileged tools (need human approval): {privileged}.\n"
        "Respond with exactly one of these forms — no markdown fences, no commentary outside the line:\n"
        '  TOOL <tool_name> {"arg": "value"}\n'
        "  FINAL <short answer for the operator>\n"
        "Use tools when you need facts (health, compose, repo). "
        "After observations appear in the user message, call more tools or FINAL.\n"
        "Never invent tool results. Prefer health_read first for health questions."
    )


def parse_model_turn(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    if not text:
        return {"type": "final", "text": ""}

    # Prefer FINAL when the model emitted tools and an answer in one completion.
    m_final_line = _FINAL_LINE_RE.search(text)
    m_tool_line = _TOOL_LINE_RE.search(text)
    if m_final_line and m_tool_line:
        return {"type": "final", "text": m_final_line.group(1).strip()}

    m = _TOOL_RE.match(text)
    if m:
        return _tool_from_match(m.group(1), m.group(2) or "{}")

    m = _FINAL_RE.match(text)
    if m:
        return {"type": "final", "text": m.group(1).strip()}

    if m_tool_line:
        return _tool_from_match(m_tool_line.group(1), m_tool_line.group(2) or "{}")

    m = _JSON_TOOL_RE.search(text)
    if m:
        return _tool_from_match(m.group(1), m.group(2))

    if m_final_line:
        return {"type": "final", "text": m_final_line.group(1).strip()}

    return {"type": "final", "text": text}


def _tool_from_match(name: str, args_raw: str) -> dict[str, Any]:
    args: dict[str, Any] = {}
    raw = args_raw.strip()
    try:
        parsed = ast.literal_eval(raw)
        if isinstance(parsed, dict):
            args = parsed
    except (SyntaxError, ValueError):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                args = parsed
        except json.JSONDecodeError:
            args = {}
    return {"type": "tool", "name": name, "args": args}


def _merge_usage(run: AgentRun, usage: dict[str, Any]) -> None:
    for key, val in usage.items():
        if isinstance(val, (int, float)):
            prev = run.usage.get(key, 0) or 0
            run.usage[key] = prev + val
        else:
            run.usage[key] = val


def step_agent_run(
    run: AgentRun,
    *,
    router: ModelRouter,
    store_put: Any,
    ctx: ToolContext | None = None,
    approved_tools: set[str] | None = None,
) -> AgentRun:
    """Advance one model→tool/final step. Persist via store_put(run)."""
    approved_tools = approved_tools if approved_tools is not None else set()
    ctx = ctx or build_tool_context()
    policy = load_policy(run.agent)

    if run.status in {
        AgentRunStatus.COMPLETED,
        AgentRunStatus.CANCELLED,
        AgentRunStatus.FAILED,
    }:
        return run

    if run.status == AgentRunStatus.AWAITING_APPROVAL and run.pending_action:
        return run

    steps = sum(1 for t in run.traces if t.get("kind") in {"model_call", "tool_result", "final"})
    if steps >= run.budget.max_steps:
        run.status = AgentRunStatus.FAILED
        run.error = "budget_exhausted:max_steps"
        run.updated_at = utcnow()
        store_put(run)
        return run

    run.status = AgentRunStatus.RUNNING
    tool_traces = [t for t in run.traces if t.get("kind") == "tool_result"]
    obs = [t.get("observation", "") for t in tool_traces]
    prompt = run.objective or "(no objective)"
    if obs:
        prompt = (
            prompt
            + "\n\nObservations from tools (use these; do not invent):\n"
            + "\n---\n".join(obs[-5:])
            + "\n\nYou already have tool results. Emit a single FINAL line summarizing them. "
            "Only emit TOOL if you need a different tool than you already used."
        )
    else:
        prompt = prompt + "\n\nNo observations yet. Emit one TOOL … line, or FINAL if no tool is needed."

    try:
        completion = router.complete(
            CompletionRequest(
                model=run.model,
                prompt=prompt,
                backend=run.backend,
                system=loop_system_prompt(policy),
            )
        )
    except PermissionError as exc:
        run.status = AgentRunStatus.FAILED
        run.error = f"provider_unavailable:{exc}"
        run.updated_at = utcnow()
        store_put(run)
        return run
    except KeyError as exc:
        run.status = AgentRunStatus.FAILED
        run.error = f"provider_unavailable:{exc}"
        run.updated_at = utcnow()
        store_put(run)
        return run
    except Exception as exc:
        from .cloud_backends import CloudUnavailable
        from .ollama_backend import OllamaUnavailable

        if isinstance(exc, (OllamaUnavailable, CloudUnavailable)):
            run.status = AgentRunStatus.FAILED
            run.error = f"provider_unavailable:{exc}"
            run.updated_at = utcnow()
            store_put(run)
            return run
        raise

    _merge_usage(run, completion.usage)
    run.traces.append(
        {
            "kind": "model_call",
            "at": utcnow(),
            "billing_class": completion.billing_class.value,
            "backend": completion.backend,
            "text": completion.text,
        }
    )

    turn = parse_model_turn(completion.text)
    if turn["type"] == "final":
        run.status = AgentRunStatus.COMPLETED
        run.final_result = turn.get("text") or completion.text
        run.traces.append({"kind": "final", "at": utcnow(), "text": run.final_result})
        run.updated_at = utcnow()
        store_put(run)
        return run

    tool_name = turn["name"]
    tool_args = turn.get("args") or {}
    action_id = str(uuid4())

    # Stop thrashing on live models that re-call the same tool with new args.
    prior_same = [t for t in tool_traces if t.get("tool") == tool_name]
    if prior_same:
        run.status = AgentRunStatus.COMPLETED
        last_obs = prior_same[-1].get("observation") or ""
        run.final_result = (
            f"(stopped repeating {tool_name}) last observation:\n{last_obs[:1500]}"
        )
        run.traces.append(
            {
                "kind": "final",
                "at": utcnow(),
                "text": run.final_result,
                "reason": "repeated_tool",
            }
        )
        run.updated_at = utcnow()
        store_put(run)
        return run

    if tool_name not in policy.allowed_tools and tool_name not in policy.privileged_tools:
        run.traces.append(
            {
                "kind": "tool_denied",
                "at": utcnow(),
                "tool": tool_name,
                "args": tool_args,
                "reason": "not_in_policy",
            }
        )
        run.status = AgentRunStatus.FAILED
        run.error = f"tool_denied:{tool_name}"
        run.updated_at = utcnow()
        store_put(run)
        return run

    if tool_needs_human_gate(
        tool_name,
        list(policy.allowed_tools),
        approved_tools,
        list(policy.privileged_tools),
    ):
        run.pending_action = {
            "id": action_id,
            "tool": tool_name,
            "args": tool_args,
            "created_at": utcnow(),
        }
        run.status = AgentRunStatus.AWAITING_APPROVAL
        run.traces.append(
            {
                "kind": "approval_required",
                "at": utcnow(),
                "action_id": action_id,
                "tool": tool_name,
                "args": tool_args,
            }
        )
        run.updated_at = utcnow()
        store_put(run)
        return run

    result = execute_allowed_tool(
        tool_name,
        tool_args,
        allowed_tools=list(policy.allowed_tools) + list(policy.privileged_tools),
        approved_tools=approved_tools,
        ctx=ctx,
    )
    run.traces.append(
        {
            "kind": "tool_result",
            "at": utcnow(),
            "tool": tool_name,
            "args": tool_args,
            "ok": result.ok,
            "denied": result.denied,
            "observation": result.observation[:4000],
        }
    )
    if result.denied:
        run.status = AgentRunStatus.FAILED
        run.error = f"tool_denied:{tool_name}"
    run.updated_at = utcnow()
    store_put(run)
    return run


def run_until_idle(
    run: AgentRun,
    *,
    router: ModelRouter,
    store_put: Any,
    ctx: ToolContext | None = None,
    approved_tools: set[str] | None = None,
    max_iterations: int | None = None,
) -> AgentRun:
    """Step until completed/failed/cancelled/awaiting_approval or iteration cap."""
    limit = max_iterations if max_iterations is not None else run.budget.max_steps + 2
    for _ in range(limit):
        before = run.status
        run = step_agent_run(
            run, router=router, store_put=store_put, ctx=ctx, approved_tools=approved_tools
        )
        if run.status in {
            AgentRunStatus.COMPLETED,
            AgentRunStatus.FAILED,
            AgentRunStatus.CANCELLED,
            AgentRunStatus.AWAITING_APPROVAL,
        }:
            return run
        if run.status == before == AgentRunStatus.RUNNING and not run.traces:
            break
    if run.status == AgentRunStatus.RUNNING:
        run.status = AgentRunStatus.FAILED
        run.error = "budget_exhausted:iterations"
        run.updated_at = utcnow()
        store_put(run)
    return run


def resolve_pending_action(
    run: AgentRun,
    *,
    decision: str,
    router: ModelRouter,
    store_put: Any,
    ctx: ToolContext | None = None,
    approved_tools: set[str] | None = None,
) -> AgentRun:
    """Approve or deny the pending tool action (IWO-007)."""
    approved_tools = set(approved_tools or [])
    pending = run.pending_action
    if not pending or run.status != AgentRunStatus.AWAITING_APPROVAL:
        run.error = "no_pending_action"
        store_put(run)
        return run

    tool_name = pending["tool"]
    tool_args = pending.get("args") or {}
    action_id = pending["id"]

    if decision != "approved":
        run.traces.append(
            {
                "kind": "action_denied",
                "at": utcnow(),
                "action_id": action_id,
                "tool": tool_name,
                "args": tool_args,
            }
        )
        run.pending_action = None
        run.status = AgentRunStatus.FAILED
        run.error = f"action_denied:{tool_name}"
        run.updated_at = utcnow()
        store_put(run)
        return run

    approved_tools.add(tool_name)
    policy = load_policy(run.agent)
    ctx = ctx or build_tool_context()
    result = execute_allowed_tool(
        tool_name,
        tool_args,
        allowed_tools=list(policy.allowed_tools) + [tool_name],
        approved_tools=approved_tools,
        ctx=ctx,
    )
    run.traces.append(
        {
            "kind": "tool_result",
            "at": utcnow(),
            "action_id": action_id,
            "tool": tool_name,
            "args": tool_args,
            "ok": result.ok,
            "observation": result.observation[:4000],
            "approved": True,
        }
    )
    run.pending_action = None
    run.status = AgentRunStatus.RUNNING
    run.updated_at = utcnow()
    store_put(run)
    return run_until_idle(
        run, router=router, store_put=store_put, ctx=ctx, approved_tools=approved_tools
    )


def cancel_agent_run(run: AgentRun, store_put: Any) -> AgentRun:
    if run.status in {AgentRunStatus.COMPLETED, AgentRunStatus.CANCELLED}:
        return run
    run.status = AgentRunStatus.CANCELLED
    run.pending_action = None
    run.error = run.error or "cancelled"
    run.updated_at = utcnow()
    store_put(run)
    return run


def retry_agent_run(run: AgentRun, store_put: Any) -> AgentRun:
    """Safe retry for failed/cancelled read-oriented runs: re-queue, keep history."""
    if run.status not in {AgentRunStatus.FAILED, AgentRunStatus.CANCELLED}:
        raise ValueError(f"retry not safe from status {run.status.value}")
    run.traces.append({"kind": "retry", "at": utcnow(), "from_status": run.status.value})
    run.status = AgentRunStatus.QUEUED
    run.error = None
    run.pending_action = None
    run.final_result = None
    run.updated_at = utcnow()
    store_put(run)
    return run


def reconcile_stuck_running(run: AgentRun, store_put: Any, *, mark: str = "failed") -> AgentRun:
    if run.status != AgentRunStatus.RUNNING:
        return run
    if mark == "queued":
        run.status = AgentRunStatus.QUEUED
        run.error = "reconciled_stuck_running"
    else:
        run.status = AgentRunStatus.FAILED
        run.error = "reconciled_stuck_running"
    run.updated_at = utcnow()
    store_put(run)
    return run
