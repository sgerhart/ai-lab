"""Execute allowlisted tools for the mini agent loop (IWO-005)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .approvals import is_privileged, requires_approval
from .mcp_client import call_mcp_tool, capability_needs_approval, get_local_server, parse_mcp_tool_name
from .memory_vault import MemoryVault, VaultError
from .operator_files import DocumentLibrary, FilesError
from .retrieval import default_retrieval_service, memory_search_tool, memory_write_tool
from .web_lookup import WebLookupError, research_pages, web_search
from .research_reports import ReportError, ReportLibrary
from .tools import ToolContext, ToolError, compose_ps_read, git_diff, git_status, health_read, repo_read, repo_search
from .workspace_isolation import apply_patch, git_commit_isolated


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


WRITE_TOOLS = frozenset(
    {
        "repo_write_bounded",
        "run_tests",
        "git_commit",
        "git_add",
        "git_push",
        "gh_pr_merge",
        "deploy",
        "apply_patch",
        "git_commit",
    }
)

_HANDLERS: dict[str, Callable[..., str]] = {
    "health_read": lambda ctx, **_a: health_read(),
    "compose_ps_read": lambda ctx, **_a: compose_ps_read(),
    "repo_read": lambda ctx, **a: repo_read(ctx, limit=int(a.get("limit", 50)), path=str(a.get("path") or "")),
    "repo_search": lambda ctx, **a: repo_search(ctx, str(a.get("query") or a.get("q") or ""), limit=int(a.get("limit", 20))),
    "git_status": lambda ctx, **_a: git_status(ctx),
    "git_diff": lambda ctx, **_a: git_diff(ctx),
    "apply_patch": lambda ctx, **a: apply_patch(ctx, str(a.get("patch") or "")),
    "git_commit": lambda ctx, **a: git_commit_isolated(ctx, str(a.get("message") or "")),
    "memory_search": lambda ctx, **a: memory_search_tool(
        str(a.get("query") or a.get("q") or ""),
        limit=int(a.get("limit", 5)),
        service=default_retrieval_service(),
    ),
    "vault_list": lambda ctx, **a: _vault_list(ctx, a),
    "vault_grep": lambda ctx, **a: _vault_grep(ctx, a),
    "vault_read": lambda ctx, **a: _vault_read(ctx, a),
    "files_list": lambda ctx, **a: _files_list(ctx, a),
    "files_grep": lambda ctx, **a: _files_grep(ctx, a),
    "files_read": lambda ctx, **a: _files_read(ctx, a),
    "web_search": lambda ctx, **a: _web_search(ctx, a),
    "research": lambda ctx, **a: _research(ctx, a),
    "report_list": lambda ctx, **a: _report_list(ctx, a),
    "report_read": lambda ctx, **a: _report_read(ctx, a),
    "report_write": lambda ctx, **a: _report_write(ctx, a),
    "memory_write": lambda ctx, **a: memory_write_tool(
        str(a.get("text") or ""),
        str(a.get("source") or ""),
        doc_id=(str(a["id"]) if a.get("id") else None),
        service=default_retrieval_service(),
    ),
    "git_push": lambda ctx, **_a: _refuse_privileged("git_push"),
    "deploy": lambda ctx, **_a: _refuse_privileged("deploy"),
    "gh_pr_merge": lambda ctx, **_a: _refuse_privileged("gh_pr_merge"),
}


def _vault_of(ctx: ToolContext) -> MemoryVault:
    return MemoryVault(ctx.vault_root)


def _bounded_limit(value: object, default: int, cap: int) -> int:
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        parsed = default
    return max(1, min(parsed, cap))


def _vault_list(ctx: ToolContext, args: dict[str, Any]) -> str:
    try:
        return _vault_of(ctx).list_files(
            str(args.get("prefix") or args.get("path") or ""),
            limit=_bounded_limit(args.get("limit"), 200, 200),
        )
    except VaultError as exc:
        raise ToolError(str(exc)) from exc


def _vault_grep(ctx: ToolContext, args: dict[str, Any]) -> str:
    try:
        return _vault_of(ctx).grep(
            str(args.get("query") or args.get("q") or ""),
            limit=_bounded_limit(args.get("limit"), 8, 20),
        )
    except VaultError as exc:
        raise ToolError(str(exc)) from exc


def _vault_read(ctx: ToolContext, args: dict[str, Any]) -> str:
    try:
        return _vault_of(ctx).read(str(args.get("path") or args.get("file") or ""))
    except VaultError as exc:
        raise ToolError(str(exc)) from exc


def _files_of(ctx: ToolContext) -> DocumentLibrary:
    return DocumentLibrary(ctx.files_root)


def _files_list(ctx: ToolContext, args: dict[str, Any]) -> str:
    try:
        return _files_of(ctx).list_files(
            str(args.get("prefix") or args.get("path") or ""),
            limit=_bounded_limit(args.get("limit"), 200, 200),
        )
    except FilesError as exc:
        raise ToolError(str(exc)) from exc


def _files_grep(ctx: ToolContext, args: dict[str, Any]) -> str:
    try:
        return _files_of(ctx).grep(
            str(args.get("query") or args.get("q") or ""),
            limit=_bounded_limit(args.get("limit"), 8, 20),
        )
    except FilesError as exc:
        raise ToolError(str(exc)) from exc


def _files_read(ctx: ToolContext, args: dict[str, Any]) -> str:
    try:
        return _files_of(ctx).read(str(args.get("path") or args.get("file") or ""))
    except FilesError as exc:
        raise ToolError(str(exc)) from exc


def _web_search(ctx: ToolContext, args: dict[str, Any]) -> str:
    if args.get("url") or args.get("href"):
        return "web_search does not open a URL from the question. Ask in words."
    try:
        return web_search(
            str(args.get("query") or args.get("q") or ""),
            opener=ctx.web_opener,
            resolve=ctx.web_resolve,
        )
    except WebLookupError as exc:
        raise ToolError(str(exc)) from exc


def _research(ctx: ToolContext, args: dict[str, Any]) -> str:
    if args.get("url") or args.get("href"):
        return "research does not open a URL from the question. Ask in words."
    query = str(args.get("query") or args.get("q") or "")
    try:
        brief, sources = research_pages(
            query,
            opener=ctx.web_opener,
            resolve=ctx.web_resolve,
        )
    except WebLookupError as exc:
        raise ToolError(str(exc)) from exc
    if not sources:
        return brief
    try:
        rel = ReportLibrary().add_dossier(str(args.get("name") or query), query, sources)
    except ReportError as exc:
        raise ToolError(str(exc)) from exc
    return brief + f"\ndossier: {rel}"


def _report_list(_ctx: ToolContext, args: dict[str, Any]) -> str:
    try:
        return ReportLibrary().list_reports(limit=_bounded_limit(args.get("limit"), 100, 200))
    except ReportError as exc:
        raise ToolError(str(exc)) from exc


def _report_read(_ctx: ToolContext, args: dict[str, Any]) -> str:
    try:
        return ReportLibrary().read(
            str(args.get("name") or args.get("path") or args.get("file") or ""),
            offset=_bounded_limit(args.get("offset"), 0, 48_000) if args.get("offset") else 0,
        )
    except ReportError as exc:
        raise ToolError(str(exc)) from exc


def _report_write(_ctx: ToolContext, args: dict[str, Any]) -> str:
    try:
        return ReportLibrary().write(
            str(args.get("name") or args.get("path") or ""),
            str(args.get("body") or args.get("text") or ""),
        )
    except ReportError as exc:
        raise ToolError(str(exc)) from exc


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
        if name in WRITE_TOOLS:
            return ToolResult(
                name=name,
                ok=False,
                observation=f"write tool denied in read-only harness: {name}",
                denied=True,
            )
        return ToolResult(name=name, ok=False, observation=f"tool not allowed: {name}", denied=True)
    if requires_approval(name, effective_allowed, approved_tools):
        return ToolResult(
            name=name,
            ok=False,
            observation=f"tool requires approval: {name}",
            denied=True,
        )
    mcp = parse_mcp_tool_name(name)
    if mcp is not None:
        server_id, tool = mcp
        server = get_local_server(server_id)
        declared = [item["name"] for item in (server or {}).get("capabilities") or []]
        if declared and tool not in declared:
            return ToolResult(
                name=name,
                ok=False,
                observation=f"MCP tool {tool!r} is not declared on {server_id!r}",
                denied=True,
            )
        if capability_needs_approval(server_id, tool) and name not in approved_tools:
            return ToolResult(
                name=name,
                ok=False,
                observation=f"tool requires approval: {name}",
                denied=True,
            )
        try:
            result = call_mcp_tool(server_id, tool, args or {})
        except Exception as exc:  # noqa: BLE001
            return ToolResult(name=name, ok=False, observation=str(exc))
        return ToolResult(
            name=name,
            ok=bool(result.get("ok")),
            observation=str(result.get("observation") or ""),
            denied=bool(result.get("denied")),
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
