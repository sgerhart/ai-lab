"""One saved summary per Nexus book, paper, or course.

Summaries are written once and read by the shelf, chat, and the agent tool.
A later run skips a file whose size and modification time are unchanged.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable
from pathlib import Path

from .nexus_rag import chunk_epub, chunk_pdf
from .nexus_study import format_book_title


def summaries_root() -> Path:
    return Path.home() / ".ai-lab" / "nexus-summaries"


def _key(rel_path: str) -> str:
    clean = rel_path.replace("\\", "/").lstrip("/")
    return hashlib.sha256(clean.encode()).hexdigest()


def _file(rel_path: str, root: Path) -> Path:
    return root / f"{_key(rel_path)}.json"


def load_summary(rel_path: str, *, root: Path | None = None) -> str:
    """Return the saved summary for a library-relative path, or an empty string."""
    if not rel_path:
        return ""
    path = _file(rel_path, root or summaries_root())
    if not path.is_file():
        return ""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    if not isinstance(data, dict):
        return ""
    return str(data.get("summary") or "").strip()


def list_summaries(*, root: Path | None = None) -> list[dict[str, str]]:
    """Every saved summary as path, title, and text."""
    base = root or summaries_root()
    if not base.is_dir():
        return []
    rows: list[dict[str, str]] = []
    for path in sorted(base.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        rel = str(data.get("path") or "")
        text = str(data.get("summary") or "").strip()
        if rel and text:
            rows.append({"path": rel, "title": str(data.get("title") or ""), "summary": text})
    return rows


def summary_is_current(rel_path: str, source: Path, *, root: Path | None = None) -> bool:
    """True when a saved summary still matches this file's size and mtime."""
    path = _file(rel_path, root or summaries_root())
    if not path.is_file():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        stat = source.stat()
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(data, dict) or not str(data.get("summary") or "").strip():
        return False
    return data.get("source_size") == stat.st_size and data.get("source_mtime_ns") == stat.st_mtime_ns


def save_summary(
    rel_path: str,
    source: Path,
    summary: str,
    *,
    title: str = "",
    root: Path | None = None,
) -> None:
    text = re.sub(r"\s+", " ", summary).strip()
    if not text:
        raise ValueError("empty summary")
    base = root or summaries_root()
    base.mkdir(parents=True, exist_ok=True)
    stat = source.stat()
    payload = {
        "path": rel_path.replace("\\", "/").lstrip("/"),
        "title": title or format_book_title(source.name),
        "summary": text[:600],
        "source_size": stat.st_size,
        "source_mtime_ns": stat.st_mtime_ns,
    }
    _file(rel_path, base).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def opening_text(source: Path, rel_path: str, *, limit: int = 1800) -> str:
    """Opening prose from an EPUB or PDF, used once as the summary source."""
    title = format_book_title(source.name)
    if source.suffix.lower() == ".epub":
        chunks = chunk_epub(source, rel_path, title)
    elif source.suffix.lower() == ".pdf":
        chunks = chunk_pdf(source, rel_path, title)
    else:
        return ""
    parts: list[str] = []
    used = 0
    for chunk in chunks:
        if used >= limit:
            break
        parts.append(chunk.text)
        used += len(chunk.text)
    return re.sub(r"\s+", " ", " ".join(parts)).strip()[:limit]


def summary_from_excerpt(
    title: str,
    excerpt: str,
    complete: Callable[[str, str], str],
) -> str:
    """Ask the supplied model for a two or three sentence summary of one excerpt."""
    body = re.sub(r"\s+", " ", excerpt).strip()
    if len(body) < 80:
        return ""
    text = complete(title, body[:1800])
    cleaned = re.sub(r"\s+", " ", text or "").strip().strip('"')
    return cleaned[:600]
