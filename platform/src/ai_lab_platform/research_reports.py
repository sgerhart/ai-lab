"""Research reports the personal agent can write and revise.

Reports live under ``~/.ai-lab/reports``, outside Git, the memory vault, and
the notes folder. A source dossier is written by the lab. The model writes
and replaces the report itself. Nothing here deletes a file.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

_SLUG_RE = re.compile(r"[^a-z0-9]+")
_MAX_BODY = 48_000
_READ_CHUNK = 8_000
_DOSSIER_CAP = 80_000
_SOURCE_BODY = 6_000


class ReportError(ValueError):
    """A report path or argument the agent must not follow."""


def default_reports_root() -> Path:
    override = os.environ.get("AI_LAB_REPORTS_ROOT", "").strip()
    if override:
        return Path(override).expanduser()
    return Path.home() / ".ai-lab" / "reports"


class ReportLibrary:
    def __init__(self, root: Path | None = None) -> None:
        self.root = (root or default_reports_root()).expanduser()

    def list_reports(self, *, limit: int = 100) -> str:
        root = self._existing_root()
        if root is None:
            return "report_list hits=0\nno reports yet"
        rows: list[str] = []
        for path in _markdown_files(root):
            rows.append(path.relative_to(root).as_posix())
            if len(rows) >= limit:
                break
        if not rows:
            return "report_list hits=0"
        return f"report_list hits={len(rows)}\n" + "\n".join(rows)

    def read(self, name: str, *, offset: int = 0) -> str:
        root = self._existing_root()
        if root is None:
            raise ReportError("no reports yet")
        path = _confine(root, _file_name(name))
        if path.is_symlink():
            raise ReportError("report symlinks are not read")
        if not path.is_file():
            raise ReportError(f"no such report: {path.name}")
        text = path.read_text(encoding="utf-8")
        start = _offset(offset)
        chunk = text[start : start + _READ_CHUNK]
        rel = path.relative_to(root).as_posix()
        lines = [f"{rel} chars={len(text)} offset={start}", chunk]
        if start + len(chunk) < len(text):
            lines.append(f"more offset={start + len(chunk)}")
        return "\n".join(lines)

    def write(self, name: str, body: str) -> str:
        rel = _file_name(name)
        if rel.endswith(".sources.md"):
            raise ReportError("source dossiers are written by research, not report_write")
        text = (body or "").strip()
        if not text:
            raise ReportError("report body is empty")
        if len(text) > _MAX_BODY:
            raise ReportError("report body is too long")
        self.root.mkdir(parents=True, exist_ok=True)
        path = _confine(self.root.resolve(), rel)
        if path.is_symlink():
            raise ReportError("report symlinks are not written")
        path.write_text(text + "\n", encoding="utf-8")
        return f"report_write path={rel} chars={len(text)}"

    def add_dossier(self, name: str, query: str, sources: list[dict[str, str]]) -> str:
        if not sources:
            raise ReportError("nothing to file")
        stem = _file_name(name)[:-3]
        rel = f"{stem}.sources.md"
        self.root.mkdir(parents=True, exist_ok=True)
        path = _confine(self.root.resolve(), rel)
        if path.is_symlink():
            raise ReportError("report symlinks are not written")
        block = _dossier_block(query, sources)
        if path.is_file():
            existing = path.read_text(encoding="utf-8")
            if len(existing) >= _DOSSIER_CAP:
                return f"{rel} dossier is full"
            path.write_text(existing.rstrip() + "\n\n" + block, encoding="utf-8")
        else:
            path.write_text(f"# Sources\n\n{block}", encoding="utf-8")
        return rel

    def _existing_root(self) -> Path | None:
        if not self.root.is_dir():
            return None
        return self.root.resolve()


def _dossier_block(query: str, sources: list[dict[str, str]]) -> str:
    lines = [f"## Query\n{query.strip()}", ""]
    for index, source in enumerate(sources, start=1):
        title = source.get("title") or "untitled"
        lines.append(f"## {index}. {title}")
        lines.append(f"- url: {source.get('url') or ''}")
        if source.get("document_date"):
            lines.append(f"- document_date: {source['document_date']}")
        if source.get("error"):
            lines.append(f"- error: {source['error']}")
        body = " ".join((source.get("body") or "").split())[:_SOURCE_BODY]
        if body:
            lines.append("")
            lines.append(body)
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _file_name(name: str) -> str:
    raw = (name or "").strip()
    if not raw:
        raise ReportError("report name is empty")
    if any(mark in raw for mark in ("/", "\\", "..")) or raw.startswith("~"):
        raise ReportError("report name escapes the reports folder")
    stem = raw[:-3] if raw.lower().endswith(".md") else raw
    slug = _SLUG_RE.sub("-", stem.casefold()).strip("-")
    if not slug:
        raise ReportError("report name is empty")
    return slug[:48].strip("-") + ".md"


def _offset(value: object) -> int:
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0
    return max(0, parsed)


def _confine(root: Path, rel: str) -> Path:
    if not rel or "/" in rel or "\\" in rel or ".." in rel:
        raise ReportError("report name escapes the reports folder")
    root_r = root.resolve()
    candidate = (root_r / rel).resolve()
    try:
        candidate.relative_to(root_r)
    except ValueError as exc:
        raise ReportError("report name escapes the reports folder") from exc
    return candidate


def _markdown_files(root: Path) -> list[Path]:
    found: list[Path] = []
    root_r = root.resolve()
    for path in sorted(root_r.glob("*.md")):
        if path.is_symlink():
            continue
        try:
            resolved = path.resolve()
            resolved.relative_to(root_r)
        except (OSError, ValueError):
            continue
        found.append(resolved)
    return found
