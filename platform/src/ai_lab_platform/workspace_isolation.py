"""Isolated git worktrees for coding writes.

Patches and commits are refused on the primary checkout. Push is not provided here.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from uuid import uuid4

from .tools import ToolContext, ToolError, resolve_scope

MARKER = ".ai-lab-isolated"


def worktrees_root() -> Path:
    raw = os.environ.get("AI_LAB_WORKTREES", "").strip()
    root = Path(raw).expanduser() if raw else Path.home() / ".ai-lab" / "worktrees"
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def create_isolated_copy(source: Path, parent: Path | None = None) -> dict[str, str]:
    """Make a detached worktree the coding run may patch. Returns id + path."""
    base = (parent or worktrees_root()).resolve()
    base.mkdir(parents=True, exist_ok=True)
    worktree_id = uuid4().hex[:12]
    dest = base / worktree_id
    prepare_worktree(source, dest)
    return {"id": worktree_id, "path": str(dest), "isolated": "true"}


def resolve_worktree(worktree_id: str, parent: Path | None = None) -> Path:
    token = (worktree_id or "").strip()
    if len(token) != 12 or any(c not in "0123456789abcdef" for c in token):
        raise ToolError("invalid worktree id")
    base = (parent or worktrees_root()).resolve()
    path = (base / token).resolve()
    if base not in path.parents:
        raise ToolError("invalid worktree id")
    if not (path / MARKER).is_file():
        raise ToolError("not an isolated worktree")
    return path


def _git(cwd: Path, *args: str, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        input=input_text,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )


def prepare_worktree(source: Path, destination: Path) -> Path:
    """Create a disposable git worktree and mark it isolated. Does not touch the source index."""
    source = source.resolve()
    destination = destination.resolve()
    if destination == source or source in destination.parents:
        raise ToolError("worktree destination must sit outside the source checkout")
    if destination.exists():
        raise ToolError(f"worktree destination already exists: {destination}")
    probe = _git(source, "rev-parse", "--is-inside-work-tree")
    if probe.returncode != 0 or probe.stdout.strip() != "true":
        raise ToolError("source is not a git repository")
    destination.parent.mkdir(parents=True, exist_ok=True)
    added = subprocess.run(
        ["git", "-C", str(source), "worktree", "add", "--detach", str(destination), "HEAD"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if added.returncode != 0:
        raise ToolError((added.stderr or added.stdout or "git worktree add failed").strip())
    (destination / MARKER).write_text("isolated\n", encoding="utf-8")
    return destination


def assert_isolated_write_root(ctx: ToolContext) -> Path:
    root = resolve_scope(ctx)
    if not (root / MARKER).is_file():
        raise ToolError("refusing to write: workspace is not an isolated worktree")
    git_dir = _git(root, "rev-parse", "--git-dir")
    if git_dir.returncode != 0:
        raise ToolError("refusing to write: not a git worktree")
    git_path = Path(git_dir.stdout.strip())
    if not git_path.is_absolute():
        git_path = (root / git_path).resolve()
    if "worktrees" not in git_path.as_posix().split("/"):
        raise ToolError("refusing to write outside a git worktree")
    return root


def _patch_paths_stay_inside(patch: str) -> None:
    for line in patch.splitlines():
        if not (line.startswith("+++ ") or line.startswith("--- ")):
            continue
        raw = line[4:].strip()
        if raw in {"/dev/null"}:
            continue
        if raw.startswith("a/") or raw.startswith("b/"):
            raw = raw[2:]
        if raw.startswith("/") or raw.startswith("~") or ".." in Path(raw).parts:
            raise ToolError(f"patch path escapes workspace: {raw}")


def apply_patch(ctx: ToolContext, patch: str) -> str:
    root = assert_isolated_write_root(ctx)
    diff = patch or ""
    if not diff.strip():
        raise ToolError("empty patch")
    if "\x00" in diff:
        raise ToolError("invalid patch")
    _patch_paths_stay_inside(diff)
    if not diff.endswith("\n"):
        diff += "\n"
    checked = subprocess.run(
        ["git", "apply", "--check", "-"],
        cwd=root,
        input=diff,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    if checked.returncode != 0:
        raise ToolError((checked.stderr or "git apply --check failed").strip())
    applied = subprocess.run(
        ["git", "apply", "-"],
        cwd=root,
        input=diff,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    if applied.returncode != 0:
        raise ToolError((applied.stderr or "git apply failed").strip())
    return "patch applied in isolated worktree"


def git_commit_isolated(ctx: ToolContext, message: str) -> str:
    root = assert_isolated_write_root(ctx)
    msg = (message or "").strip()
    if not msg or "\n" in msg or len(msg) > 200:
        raise ToolError("commit message must be one line, 1–200 characters")
    added = _git(root, "add", "-A")
    if added.returncode != 0:
        raise ToolError((added.stderr or "git add failed").strip())
    committed = _git(
        root,
        "-c",
        "user.email=ai-lab@localhost",
        "-c",
        "user.name=ai-lab",
        "commit",
        "-m",
        msg,
    )
    if committed.returncode != 0:
        raise ToolError((committed.stderr or committed.stdout or "git commit failed").strip())
    return committed.stdout.strip() or "committed"
