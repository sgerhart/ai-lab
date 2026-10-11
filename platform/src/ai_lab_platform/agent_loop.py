"""Bounded, robust agent model/tool loop and second-brain harness (FEAT-010 / IWO-005 / IWO-102).

Runs on the control plane. Evaluates model completions, parses structured tool calls,
supports reasoning/thought extraction, injects memory vault context, and executes
governed tools with human approval gates.
"""

from __future__ import annotations

import ast
import json
import re
from typing import Any
from uuid import uuid4

from .conversation import AgentRun, AgentRunStatus, Message, MessageRole
from .mcp_client import binding_allows, bound_agent_tool_names, capability_needs_approval, parse_mcp_tool_name
from .model_router import CompletionRequest, ModelRouter
from .model_slot import ModelSlotBusy
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
_MARKDOWN_JSON_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)
_THINK_TAG_RE = re.compile(r"<think>(.*?)</think>", re.DOTALL | re.IGNORECASE)

_HISTORY_MESSAGES = 10
_HISTORY_LINE = 500
_HISTORY_CAP = 3200
_OBSERVATION_CAP = 9_000


def _account_tool_block(objective: str, tool_name: str) -> str | None:
    """Lab memory is the repository, not an outside account."""
    from .agent_builder import external_account

    if not external_account(objective or ""):
        return None
    if tool_name in {"memory_search", "memory_write", "http_get_allowlist", "write_report_artifact"}:
        return (
            "The AI Lab repository is this lab's own code and notes. "
            "It is not a Gmail account. This run stops instead of citing a work order. "
            "Connect the mailbox before the agent can read it."
        )
    return None


_REPEATABLE_TOOLS = frozenset(
    {
        "vault_list",
        "vault_grep",
        "vault_read",
        "files_list",
        "files_grep",
        "files_read",
        "web_search",
        "research",
        "report_list",
        "report_read",
        "report_write",
        "memory_search",
        "repo_search",
        "repo_read",
    }
)


def _call_key(args: dict[str, Any]) -> str:
    try:
        return json.dumps(args, sort_keys=True, default=str)
    except TypeError:
        return str(sorted(args.items()))


def _repeat_blocks(tool_name: str, tool_args: dict[str, Any], tool_traces: list[dict[str, Any]]) -> bool:
    prior = [trace for trace in tool_traces if trace.get("tool") == tool_name]
    if not prior:
        return False
    if tool_name not in _REPEATABLE_TOOLS:
        return True
    key = _call_key(tool_args)
    return any(_call_key(trace.get("args") or {}) == key for trace in prior)


def loop_system_prompt(
    policy: AgentPolicy,
    mcp_tools: list[str] | None = None,
    extra_tools: list[str] | None = None,
    brief: str = "",
) -> str:
    """Instruct live models to operate as an intelligent collaborator and use structured tool forms."""
    allowed_names = list(policy.allowed_tools)
    for name in extra_tools or []:
        if name not in allowed_names:
            allowed_names.append(name)
    allowed = ", ".join(allowed_names) or "(none)"
    privileged = ", ".join(policy.privileged_tools) or "(none)"
    mcp = ", ".join(mcp_tools or []) or "(none)"
    return (
        f"You are the {policy.id} agent for ai-lab on the Mac mini control plane.\n"
        f"Role: High-intelligence autonomous collaborator and second brain.\n"
        f"Isolation tier {policy.isolation_tier}; read_only={policy.read_only}.\n"
        f"Allowed tools (no approval): {allowed}.\n"
        f"Privileged tools (need human approval): {privileged}.\n"
        f"MCP tools (operator-listed servers): {mcp}.\n\n"
        "Tool Execution Protocol:\n"
        "To invoke a tool, respond with either:\n"
        '  TOOL <tool_name> {"arg": "value"}\n'
        '  or a JSON tool call block: {"type": "tool", "name": "<tool_name>", "args": {...}}\n'
        "When you have finished gathering data and are ready to provide your complete answer, respond with:\n"
        "  FINAL <your comprehensive guidance and findings>\n\n"
        "Principles:\n"
        "1. The AI Lab repository contains the lab's local code and notes. It is not an email or personal third-party account.\n"
        "2. Use research and web_search for public information; use vault_read / vault_grep for your second brain memory.\n"
        "3. Use report_write to compile multi-source reports and dossiers when conducting deep research.\n"
        "4. Never hallucinate tool outputs. Citing exact facts from observations is mandatory."
    ) + _brief_block(brief)


def _clip_line(text: str) -> str:
    return " ".join((text or "").split())[:_HISTORY_LINE]


def earlier_turns(messages: list[Message], objective: str) -> str:
    """Prior user and assistant lines. The current question is not repeated."""
    kept: list[tuple[str, str]] = []
    for message in messages:
        if message.role not in {MessageRole.USER, MessageRole.ASSISTANT}:
            continue
        text = _clip_line(message.content)
        if not text:
            continue
        kept.append((message.role.value, text))
    if kept and kept[-1][0] == "user" and kept[-1][1] == _clip_line(objective):
        kept.pop()
    chosen = kept[-_HISTORY_MESSAGES:]
    if not chosen:
        return ""
    return "\n".join(f"{role}: {text}" for role, text in chosen)[:_HISTORY_CAP]


def conversation_history(store: Any, run: AgentRun) -> str:
    """Earlier lines for a personal run. Other agents get an empty string."""
    if run.agent != "personal" or not (run.conversation_id or "").strip():
        return ""
    if not hasattr(store, "list_messages"):
        return ""
    return earlier_turns(store.list_messages(run.conversation_id), run.objective)


def _brief_block(brief: str) -> str:
    text = (brief or "").strip()
    if not text:
        return ""
    return (
        "\n\nPersonal memory brief (Second Brain Context):\n"
        "vault tools, files tools, web_search, and research may be called again with different arguments. "
        "report_read and report_write may be called to compile or revise dossiers.\n"
        + text
    )


def extract_thought_and_content(text: str) -> tuple[str, str]:
    """Extract reasoning <think>...</think> tags and the remaining actionable text."""
    thoughts: list[str] = []
    def _collect(m: re.Match[str]) -> str:
        thoughts.append(m.group(1).strip())
        return ""

    cleaned = _THINK_TAG_RE.sub(_collect, text).strip()
    thought_summary = "\n\n".join(thoughts).strip()
    return thought_summary, cleaned


def parse_model_turn(text: str) -> dict[str, Any]:
    raw_text = (text or "").strip()
    if not raw_text:
        return {"type": "final", "text": ""}

    # Strip thinking blocks for turn parsing
    _, cleaned_text = extract_thought_and_content(raw_text)
    candidate = cleaned_text if cleaned_text else raw_text

    # 1. Prefer FINAL when the model emitted tools and an answer in one completion.
    m_final_line = _FINAL_LINE_RE.search(candidate)
    m_tool_line = _TOOL_LINE_RE.search(candidate)
    if m_final_line and m_tool_line:
        return {"type": "final", "text": m_final_line.group(1).strip()}

    # 2. Check exact / line-anchored TOOL syntax
    m = _TOOL_RE.match(candidate)
    if m:
        return _tool_from_match(m.group(1), m.group(2) or "{}")

    # 3. Check exact FINAL syntax
    m = _FINAL_RE.match(candidate)
    if m:
        return {"type": "final", "text": m.group(1).strip()}

    # 4. Check embedded TOOL line
    if m_tool_line:
        return _tool_from_match(m_tool_line.group(1), m_tool_line.group(2) or "{}")

    # 5. Check markdown codeblock with JSON tool call
    m_md = _MARKDOWN_JSON_RE.search(candidate)
    if m_md:
        try:
            parsed = json.loads(m_md.group(1))
            if isinstance(parsed, dict):
                if parsed.get("type") == "tool" and "name" in parsed:
                    return {"type": "tool", "name": parsed["name"], "args": parsed.get("args") or {}}
                if "name" in parsed and ("args" in parsed or "arguments" in parsed):
                    return {"type": "tool", "name": parsed["name"], "args": parsed.get("args") or parsed.get("arguments") or {}}
                if "function" in parsed and isinstance(parsed["function"], dict):
                    fn = parsed["function"]
                    args = fn.get("arguments") or fn.get("args") or {}
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except Exception:
                            args = {}
                    return {"type": "tool", "name": fn.get("name", ""), "args": args}
        except Exception:
            pass

    # 6. Check JSON tool regex
    m = _JSON_TOOL_RE.search(candidate)
    if m:
        return _tool_from_match(m.group(1), m.group(2))

    # 7. Check embedded FINAL line
    if m_final_line:
        return {"type": "final", "text": m_final_line.group(1).strip()}

    # Fallback to final answer
    return {"type": "final", "text": candidate}


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
    history: str = "",
) -> AgentRun:
    """Advance one model→tool/final step. Persist via store_put(run)."""
    approved_tools = approved_tools if approved_tools is not None else set()
    ctx = ctx or build_tool_context()
    policy = load_policy(run.agent)
    if policy.id == "personal" and ctx.vault_root is None:
        from .memory_vault import default_vault_root

        ctx.vault_root = default_vault_root()

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
    follow = (
        "vault tools, files tools, web_search, and research may be called again with different arguments. "
        "report_read and report_write may be called again to revise a report. "
        "Otherwise emit a single FINAL line."
        if policy.id == "personal"
        else "Only emit TOOL if you need a different tool than you already used."
    )
    prompt = run.objective or "(no objective)"
    if policy.id == "personal" and (history or "").strip():
        prompt = (
            "Earlier in this conversation:\n"
            + history.strip()
            + "\n\nCurrent question:\n"
            + prompt
        )
    if obs:
        prompt = (
            prompt
            + "\n\nObservations from tools (use these; do not invent):\n"
            + "\n---\n".join(obs[-5:])
            + "\n\nYou already have tool results. Emit a single FINAL line summarizing them. "
            + follow
        )
    else:
        prompt = prompt + "\n\nNo observations yet. Emit one TOOL … line, or FINAL if no tool is needed."

    mcp_tools = bound_agent_tool_names(run.agent, list(run.mcp_server_ids or [])) if run.mcp_server_ids else []
    from .tool_catalog import extra_read_tools

    granted = extra_read_tools(list(getattr(run, "granted_tools", []) or []))
    effective_allowed = list(policy.allowed_tools) + granted + list(policy.privileged_tools) + mcp_tools
    brief = ""
    if policy.id == "personal":
        from .memory_vault import MemoryVault

        brief = MemoryVault(ctx.vault_root).render_brief()

    try:
        completion = router.complete(
            CompletionRequest(
                model=run.model,
                prompt=prompt,
                backend=run.backend,
                system=loop_system_prompt(policy, mcp_tools=mcp_tools, extra_tools=granted, brief=brief),
            )
        )
    except ModelSlotBusy as exc:
        run.status = AgentRunStatus.QUEUED
        run.error = None
        run.usage["model_slot"] = {"state": "waiting", "note": str(exc)}
        run.traces = [t for t in run.traces if t.get("kind") != "model_wait"]
        run.traces.append({"kind": "model_wait", "at": utcnow(), "observation": str(exc)})
        run.updated_at = utcnow()
        store_put(run)
        return run
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

    thought, _ = extract_thought_and_content(completion.text)
    if thought:
        run.traces.append({"kind": "model_thought", "at": utcnow(), "thought": thought})

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
    blocked = _account_tool_block(run.objective, tool_name)
    if blocked:
        run.status = AgentRunStatus.COMPLETED
        run.final_result = blocked
        run.traces.append({"kind": "final", "at": utcnow(), "text": blocked, "reason": "account_not_connected"})
        run.updated_at = utcnow()
        store_put(run)
        return run
    action_id = str(uuid4())

    # Lab tools stop on a repeated name. Vault reads may run again with new arguments.
    if _repeat_blocks(tool_name, tool_args, tool_traces):
        run.status = AgentRunStatus.COMPLETED
        prior_same = [trace for trace in tool_traces if trace.get("tool") == tool_name]
        last_obs = (prior_same[-1].get("observation") if prior_same else "") or ""
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

    if (
        tool_name not in policy.allowed_tools
        and tool_name not in policy.privileged_tools
        and tool_name not in mcp_tools
        and tool_name not in granted
        and parse_mcp_tool_name(tool_name) is None
    ):
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

    # Listed MCP tools run only when this agent is bound to that capability.
    mcp_parsed = parse_mcp_tool_name(tool_name)
    if mcp_parsed is not None:
        sid, mcp_tool = mcp_parsed
        if sid not in (run.mcp_server_ids or []):
            run.traces.append(
                {
                    "kind": "tool_denied",
                    "at": utcnow(),
                    "tool": tool_name,
                    "args": tool_args,
                    "reason": "mcp_server_not_on_run",
                }
            )
            run.status = AgentRunStatus.FAILED
            run.error = f"tool_denied:{tool_name}"
            run.updated_at = utcnow()
            store_put(run)
            return run
        if not binding_allows(sid, run.agent, mcp_tool):
            run.traces.append(
                {
                    "kind": "tool_denied",
                    "at": utcnow(),
                    "tool": tool_name,
                    "args": tool_args,
                    "reason": "mcp_not_bound",
                }
            )
            run.status = AgentRunStatus.FAILED
            run.error = f"tool_denied:{tool_name}"
            run.updated_at = utcnow()
            store_put(run)
            return run
        if tool_name not in effective_allowed:
            effective_allowed.append(tool_name)
        if capability_needs_approval(sid, mcp_tool) and tool_name not in approved_tools:
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
            allowed_tools=effective_allowed,
            approved_tools=approved_tools | {tool_name},
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
                "observation": result.observation[:_OBSERVATION_CAP],
            }
        )
        if result.denied:
            run.status = AgentRunStatus.FAILED
            run.error = f"tool_denied:{tool_name}"
        run.updated_at = utcnow()
        store_put(run)
        return run

    if tool_needs_human_gate(
        tool_name,
        list(policy.allowed_tools) + granted + mcp_tools,
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
        allowed_tools=effective_allowed,
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
            "observation": result.observation[:_OBSERVATION_CAP],
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
    history: str = "",
) -> AgentRun:
    """Step until completed/failed/cancelled/awaiting_approval or iteration cap."""
    limit = max_iterations if max_iterations is not None else run.budget.max_steps + 2
    for _ in range(limit):
        before = run.status
        run = step_agent_run(
            run,
            router=router,
            store_put=store_put,
            ctx=ctx,
            approved_tools=approved_tools,
            history=history,
        )
        if run.status in {
            AgentRunStatus.COMPLETED,
            AgentRunStatus.FAILED,
            AgentRunStatus.CANCELLED,
            AgentRunStatus.AWAITING_APPROVAL,
            AgentRunStatus.QUEUED,
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
            "observation": result.observation[:_OBSERVATION_CAP],
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
