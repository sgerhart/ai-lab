"""Read-only notes folder for the personal agent.

Files live under ``~/.ai-lab/files``, outside Git and outside the memory vault.
The agent can list, search, and read ``.md`` and ``.txt`` files. It cannot write them.
"""

from __future__ import annotations

import os
from pathlib import Path

_MAX_FILE_BYTES = 256_000
_READ_CAP = 8_000
_SUFFIXES = {".md", ".txt"}
_README = """# Files

Put notes here as `.md` or `.txt`. The personal agent can list, search, and read
this folder. It cannot change these files. This folder is not the memory vault.
"""


class FilesError(ValueError):
    """A files-folder path or argument the agent must not follow."""


def default_files_root() -> Path:
    override = os.environ.get("AI_LAB_FILES_ROOT", "").strip()
    if override:
        return Path(override).expanduser()
    return Path.home() / ".ai-lab" / "files"


class DocumentLibrary:
    def __init__(self, root: Path | None = None) -> None:
        self.root = (root or default_files_root()).expanduser()

    def ensure_folder(self) -> None:
        """Create the folder and a short README. Existing files stay."""
        self.root.mkdir(parents=True, exist_ok=True)
        readme = self.root / "README.md"
        if not readme.exists():
            readme.write_text(_README, encoding="utf-8")

    def list_files(self, prefix: str = "", *, limit: int = 200) -> str:
        root = self._existing_root()
        if root is None:
            return "files_list hits=0\nfiles folder has no files yet"
        rel_prefix = _safe_prefix(prefix)
        rows: list[str] = []
        for path in _text_files(root):
            rel = path.relative_to(root).as_posix()
            if rel_prefix and rel != rel_prefix and not rel.startswith(rel_prefix + "/"):
                continue
            rows.append(rel)
            if len(rows) >= limit:
                break
        if not rows:
            return f"files_list hits=0 prefix={rel_prefix or '/'}"
        return f"files_list hits={len(rows)} prefix={rel_prefix or '/'}\n" + "\n".join(rows)

    def grep(self, query: str, *, limit: int = 8) -> str:
        needle = _query(query)
        root = self._existing_root()
        if root is None:
            return f"files_grep query={needle} hits=0\nfiles folder has no files yet"
        ranked: list[tuple[str, list[str]]] = []
        folded = needle.casefold()
        for path in _text_files(root):
            text = _read_capped(path)
            if text is None or folded not in text.casefold():
                continue
            rel = path.relative_to(root).as_posix()
            lines = _matching_lines(text, needle)[:3]
            ranked.append((rel, lines))
        ranked.sort(key=lambda item: item[0])
        chosen = ranked[:limit]
        if not chosen:
            return f"files_grep query={needle} hits=0"
        blocks = [f"files_grep query={needle} hits={len(chosen)}"]
        for rel, lines in chosen:
            blocks.append(rel)
            blocks.extend(lines)
        return "\n".join(blocks)[:_READ_CAP]

    def read(self, rel: str) -> str:
        root = self._existing_root()
        if root is None:
            raise FilesError("files folder has no files yet")
        path = _confine(root, rel)
        if not path.is_file():
            raise FilesError(f"no such file: {rel}")
        if path.suffix.lower() not in _SUFFIXES:
            raise FilesError("files reads .md and .txt only")
        text = _read_capped(path)
        if text is None:
            raise FilesError("file is too large to read")
        header = path.relative_to(root).as_posix()
        return f"{header}\n{text[:_READ_CAP]}"

    def _existing_root(self) -> Path | None:
        if not self.root.is_dir():
            return None
        return self.root.resolve()


def _safe_prefix(prefix: str) -> str:
    raw = (prefix or "").strip().replace("\\", "/").lstrip("/")
    if not raw:
        return ""
    if ".." in Path(raw).parts:
        raise FilesError("prefix escapes the files folder")
    return raw.rstrip("/")


def _query(query: str) -> str:
    needle = " ".join((query or "").split())
    if not needle:
        raise FilesError("query is empty")
    if len(needle) > 200:
        raise FilesError("query is too long")
    return needle


def _confine(root: Path, rel: str) -> Path:
    raw = (rel or "").strip().replace("\\", "/")
    if not raw or raw.startswith("/") or raw.startswith("~"):
        raise FilesError("path escapes the files folder")
    if ".." in Path(raw).parts:
        raise FilesError("path escapes the files folder")
    root_r = root.resolve()
    candidate = (root_r / raw).resolve()
    try:
        candidate.relative_to(root_r)
    except ValueError as exc:
        raise FilesError("path escapes the files folder") from exc
    return candidate


def _matching_lines(body: str, needle: str) -> list[str]:
    folded = needle.casefold()
    found: list[str] = []
    for line in body.splitlines():
        if folded in line.casefold() and line.strip():
            found.append(line.strip()[:240])
    return found


def _read_capped(path: Path) -> str | None:
    try:
        if path.stat().st_size > _MAX_FILE_BYTES:
            return None
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None


def _text_files(root: Path) -> list[Path]:
    found: list[Path] = []
    root_r = root.resolve()
    for dirpath, dirnames, filenames in os.walk(root_r, followlinks=False):
        dirnames[:] = sorted(name for name in dirnames if not name.startswith("."))
        for name in sorted(filenames):
            if Path(name).suffix.lower() not in _SUFFIXES:
                continue
            path = Path(dirpath) / name
            if path.is_symlink():
                continue
            try:
                resolved = path.resolve()
                resolved.relative_to(root_r)
            except (OSError, ValueError):
                continue
            found.append(resolved)
    return found
