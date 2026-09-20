"""Bounded tools. No host-wide filesystem, no network unless allowlisted, no privileged exec."""

from __future__ import annotations

import socket
import subprocess
from dataclasses import dataclass
from pathlib import Path


class ToolError(RuntimeError):
    pass


class PathEscape(ToolError):
    pass


@dataclass
class ToolContext:
    workspace_root: Path
    artifact_root: Path
    bounded_scope: str = ""


def resolve_scope(ctx: ToolContext) -> Path:
    root = ctx.workspace_root.resolve()
    if not ctx.bounded_scope:
        return root
    target = (root / ctx.bounded_scope).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise PathEscape(f"bounded_scope escapes workspace: {ctx.bounded_scope}") from exc
    return target


def repo_read(ctx: ToolContext, limit: int = 50) -> str:
    target = resolve_scope(ctx)
    if not target.exists():
        raise ToolError(f"path does not exist: {target}")
    if target.is_file():
        text = target.read_text(encoding="utf-8", errors="replace")
        return text[:4000]
    names = sorted(p.name for p in target.iterdir())[:limit]
    return "\n".join(names)


def git_status(ctx: ToolContext) -> str:
    target = resolve_scope(ctx)
    result = subprocess.run(
        ["git", "-C", str(target), "status", "--porcelain"],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    if result.returncode != 0:
        raise ToolError(result.stderr.strip() or "git status failed")
    return result.stdout or "(clean)"


def write_report_artifact(ctx: ToolContext, body: str, name: str = "report.md") -> str:
    ctx.artifact_root.mkdir(parents=True, exist_ok=True)
    safe = Path(name).name
    if safe != name or "/" in name or name.startswith("."):
        raise ToolError(f"invalid artifact name: {name}")
    path = ctx.artifact_root / safe
    path.write_text(body, encoding="utf-8")
    return str(path)


def health_read(bind: str = "127.0.0.1", ports: tuple[int, ...] = (5432, 6379, 6333, 8088)) -> str:
    lines = []
    for port in ports:
        sock = socket.socket()
        sock.settimeout(0.2)
        try:
            sock.connect((bind, port))
            lines.append(f"{bind}:{port} open")
        except OSError:
            lines.append(f"{bind}:{port} closed")
        finally:
            sock.close()
    return "\n".join(lines) + "\nnote: closed is expected until compose/API are deployed"


def compose_ps_read() -> str:
    return "compose not queried from the worker (read-only stub). Use docs/runbooks/start-stop-control-plane.md"


def http_get_allowlist(_url: str) -> str:
    # Network fetch is disabled in the local worker until an allowlist of hosts is supplied.
    raise ToolError("http_get_allowlist is disabled until D-016/allowlist hosts are set; will not fabricate citations")
