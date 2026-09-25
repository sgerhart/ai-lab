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


def repo_read(ctx: ToolContext, limit: int = 50, path: str = "") -> str:
    root = resolve_scope(ctx)
    target = _resolve_relative(root, path) if path else root
    if not target.exists():
        raise ToolError(f"path does not exist: {path or '.'}")
    if target.is_file():
        text = target.read_text(encoding="utf-8", errors="replace")
        return text[:4000]
    names = sorted(p.name for p in target.iterdir() if p.name != ".git")[:limit]
    return "\n".join(names)


def repo_search(ctx: ToolContext, query: str, limit: int = 20) -> str:
    """Filename-and-content search inside the authorized workspace. Read-only."""
    needle = (query or "").strip()
    if not needle or len(needle) > 200:
        raise ToolError("query required (max 200 chars)")
    root = resolve_scope(ctx)
    if not root.is_dir():
        raise ToolError("workspace is not a directory")
    hits: list[str] = []
    skip = {".git", "__pycache__", "node_modules", ".venv"}
    for path in sorted(root.rglob("*")):
        if any(part in skip or part.startswith(".") for part in path.relative_to(root).parts):
            continue
        if not path.is_file():
            continue
        try:
            if path.stat().st_size > 200_000:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if needle in text or needle in path.name:
            hits.append(str(path.relative_to(root)))
            if len(hits) >= max(1, min(limit, 50)):
                break
    return "\n".join(hits) if hits else "(no matches)"


def _resolve_relative(root: Path, rel: str) -> Path:
    raw = (rel or "").strip()
    if not raw or raw.startswith("~") or raw.startswith("/") or "\x00" in raw:
        raise PathEscape(f"path not allowed: {rel!r}")
    target = (root / raw).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise PathEscape(f"path escapes workspace: {rel}") from exc
    return target


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


def git_diff(ctx: ToolContext) -> str:
    """Read-only diff of the authorized workspace. Does not stage or commit."""
    target = resolve_scope(ctx)
    result = subprocess.run(
        ["git", "-C", str(target), "diff", "--stat", "HEAD"],
        capture_output=True,
        text=True,
        timeout=8,
        check=False,
    )
    if result.returncode != 0:
        err = (result.stderr or "").strip()
        if "not a git repository" in err.lower():
            raise ToolError("not a git repository")
        raise ToolError(err or "git diff failed")
    stat = result.stdout.strip() or "(no unstaged diff)"
    patch = subprocess.run(
        ["git", "-C", str(target), "diff", "HEAD"],
        capture_output=True,
        text=True,
        timeout=8,
        check=False,
    )
    body = (patch.stdout or "").strip()
    if len(body) > 4000:
        body = body[:4000] + "\n…(truncated)"
    return stat if not body else f"{stat}\n\n{body}"


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
    """Read-only status for *this* repo's compose file. Does not start services."""
    root = Path(__file__).resolve().parents[3]
    compose = root / "infrastructure" / "compose.yaml"
    env = root / "infrastructure" / "compose.example.env"
    try:
        result = subprocess.run(
            [
                "docker",
                "compose",
                "-f",
                str(compose),
                "--env-file",
                str(env),
                "ps",
            ],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"compose not queried ({exc}). Expected until the M1 stack is deployed."
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "").strip()[:400]
        return f"compose ps failed (expected until deploy): {err or 'non-zero exit'}"
    body = (result.stdout or "").strip()
    return body or "ai-lab-control: no containers (expected until compose up)"


def http_get_allowlist(_url: str) -> str:
    # Network fetch is disabled in the local worker until an allowlist of hosts is supplied.
    raise ToolError("http_get_allowlist is disabled until D-016/allowlist hosts are set; will not fabricate citations")
