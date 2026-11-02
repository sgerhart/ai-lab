"""Discover Nexus books on disk and copy new ones in from iCloud.

The Study Hub catalog is a static list. Files added only to iCloud do not
appear until they are copied into the local mirror (~/.ai-lab/nexus) and the
library scan sees them. iCloud reads can stall, so every probe and copy runs
in a child process with a timeout.
"""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

from .nexus_study import find_nexus_root, format_book_title

BOOK_SUFFIXES = {".epub", ".pdf"}
CONTENT_DIRS = (
    "01_AI_and_GenAI",
    "02_Python_and_Data_Science",
    "03_Courses_and_Bootcamps",
    "04_Books_Library",
    "05_Cybersecurity",
    "06_Apple_and_Swift",
)
_CATEGORY_RULES = (
    ("04_Books_Library/Cybersecurity/", "cyber-books"),
    ("04_Books_Library/Cloud_Platform_and_eBPF/", "cloud-books"),
    ("04_Books_Library/Robotics_and_Automation/", "robotics-books"),
    ("04_Books_Library/Data_Engineering/", "python-ds"),
    ("04_Books_Library/Data_Science/", "python-ds"),
    ("04_Books_Library/", "ai-books"),
    ("02_Python_and_Data_Science/", "python-ds"),
    ("05_Cybersecurity/", "cyber-books"),
    ("01_AI_and_GenAI/05_Research_Papers/", "papers"),
    ("01_AI_and_GenAI/", "ai-books"),
    ("03_Courses_and_Bootcamps/", "courses"),
    ("06_Apple_and_Swift/", "courses"),
)
_CATEGORY_LABELS = {
    "ai-books": "AI and machine learning",
    "python-ds": "Python and data science",
    "cloud-books": "Cloud and platform",
    "cyber-books": "Cybersecurity",
    "robotics-books": "Robotics and automation",
    "papers": "Research paper",
    "courses": "Course",
}
_DIR_CHECK = "import os, sys\nraise SystemExit(0 if os.path.isdir(sys.argv[1]) else 1)\n"


def mirror_dir() -> Path:
    """Local Nexus copy the control plane serves ahead of iCloud."""
    return Path.home() / ".ai-lab" / "nexus"


def icloud_candidates() -> list[Path]:
    home = Path.home()
    return [
        home / "Library" / "Mobile Documents" / "com~apple~CloudDocs" / "Documents" / "Information",
        home / "Library" / "Mobile Documents" / "com~apple~CloudDocs" / "Information",
        home / "Documents" / "Information",
        home / "Information",
    ]


def category_for(rel_path: str) -> str:
    """Map a library-relative path to a Study Hub filter."""
    rel = rel_path.replace("\\", "/").lstrip("/")
    for prefix, category in _CATEGORY_RULES:
        if rel.startswith(prefix):
            return category
    return "ai-books"


def path_is_dir(path: Path, timeout_s: float = 5) -> bool:
    """Return whether path is a directory, giving up if the stat stalls."""
    try:
        proc = subprocess.run(
            [sys.executable, "-c", _DIR_CHECK, str(path)],
            capture_output=True,
            timeout=timeout_s,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return proc.returncode == 0


def find_icloud_source(mirror: Path | None = None) -> Path | None:
    """First iCloud Information folder that actually holds library content."""
    destination = mirror or mirror_dir()
    try:
        mirror_resolved = destination.resolve() if destination.exists() else None
    except OSError:
        mirror_resolved = None
    for candidate in icloud_candidates():
        try:
            if mirror_resolved is not None and candidate.resolve() == mirror_resolved:
                continue
        except OSError:
            continue
        if not path_is_dir(candidate):
            continue
        if any(path_is_dir(candidate / name) for name in CONTENT_DIRS):
            return candidate
    return None


def scan_library(root: Path) -> list[dict[str, object]]:
    """Group EPUB and PDF files under root into library cards."""
    if not root.is_dir():
        return []
    groups: dict[str, dict[str, object]] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in BOOK_SUFFIXES:
            continue
        rel = path.relative_to(root).as_posix()
        if any(part.startswith(".") for part in rel.split("/")):
            continue
        key = f"{path.parent.relative_to(root).as_posix()}/{path.stem}"
        entry = groups.get(key)
        if entry is None:
            category = category_for(rel)
            label = _CATEGORY_LABELS.get(category, "Library")
            entry = {
                "id": "disk-" + hashlib.sha256(key.encode()).hexdigest()[:12],
                "title": format_book_title(path.name),
                "category": category,
                "desc": f"{label} book.",
                "formats": [],
            }
            groups[key] = entry
        formats = entry["formats"]
        assert isinstance(formats, list)
        formats.append({"format": path.suffix.lower().lstrip(".").upper(), "path": rel})
    books = list(groups.values())
    for book in books:
        formats = book["formats"]
        assert isinstance(formats, list)
        formats.sort(key=lambda item: str(item["format"]))
    return books


def scan_served_library() -> dict[str, object]:
    """Scan the Nexus directory the control plane would serve."""
    root = find_nexus_root()
    books = scan_library(root) if root is not None else []
    return {"books": books, "count": len(books)}


def sync_tree(
    source: Path,
    dest: Path,
    *,
    folders: tuple[str, ...] = CONTENT_DIRS,
    apply: bool = False,
    timeout_s: int = 180,
) -> dict[str, object]:
    """Copy library folders from source into dest.

    Dry-run unless apply is true. UI files at the Information root are left
    alone. rsync is not asked to delete anything.
    """
    if shutil.which("rsync") is None:
        return {"ok": False, "apply": apply, "copied": [], "errors": ["rsync is not installed"]}
    try:
        same = source.resolve() == dest.resolve()
    except OSError:
        same = False
    if same:
        return {
            "ok": True,
            "apply": apply,
            "copied": [],
            "errors": [],
            "note": "The served library is already the iCloud folder.",
        }

    copied: list[str] = []
    errors: list[str] = []
    for folder in folders:
        src = source / folder
        if not path_is_dir(src, timeout_s=8):
            continue
        target = dest / folder
        if apply:
            target.mkdir(parents=True, exist_ok=True)
        command = [
            "rsync",
            "-a",
            "--timeout=30",
            "--out-format=%n",
            "--exclude=.*",
            "--exclude=.DS_Store",
        ]
        if not apply:
            command.append("--dry-run")
        command.extend([f"{src}/", f"{target}/"])
        try:
            proc = subprocess.run(
                command,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=timeout_s,
                check=False,
            )
        except subprocess.TimeoutExpired:
            errors.append(f"{folder} timed out")
            continue
        except OSError as exc:
            errors.append(f"{folder} failed: {exc}")
            continue
        for line in (proc.stdout or "").splitlines():
            name = line.strip()
            if not name or name.endswith("/"):
                continue
            if Path(name).suffix.lower() not in BOOK_SUFFIXES:
                continue
            copied.append(f"{folder}/{name}")
        if proc.returncode != 0:
            detail = (proc.stderr or "").strip().splitlines()
            errors.append(detail[-1] if detail else f"{folder} rsync exited {proc.returncode}")
    return {"ok": not errors, "apply": apply, "copied": copied, "errors": errors}


def _lookup_words(query: str) -> list[str]:
    stop = {"the", "and", "for", "with", "what", "how", "can", "you", "that", "this", "from", "have", "about"}
    return [word.lower() for word in re.findall(r"[A-Za-z]{3,}", query) if word.lower() not in stop]


def suggest_books(
    query: str,
    *,
    limit: int = 4,
    root: Path | None = None,
    searcher: object | None = None,
    snippet_chars: int = 220,
) -> list[dict[str, object]]:
    """Books in Nexus that can help with a question.

    Semantic hits from the book index come first. Title matches from the files
    on disk fill in when a book has not been indexed yet.
    """
    text = (query or "").strip()
    words = _lookup_words(text)
    if len(text) < 3 or not words:
        return []
    limit = max(1, min(limit, 8))
    hits: list[dict[str, object]] = []
    seen: set[str] = set()

    chunks: list[object] = []
    if searcher is not None:
        try:
            found = searcher(text, limit * 3)  # type: ignore[operator]
        except (OSError, RuntimeError, ValueError, TypeError):
            found = []
        chunks = list(found or [])
    else:
        try:
            from .nexus_rag import NexusRagStore

            chunks = list(NexusRagStore(timeout=0.8).search(text, limit=limit * 3))
        except Exception:
            chunks = []
    if chunks and float(getattr(chunks[0], "score", 0) or 0) < 0.2:
        chunks = []
    for chunk in chunks:
        score = float(getattr(chunk, "score", 0) or 0)
        rel = str(getattr(chunk, "rel_path", "") or "")
        title = str(getattr(chunk, "title", "") or "")
        key = rel or title
        if not key or key in seen:
            continue
        seen.add(key)
        snippet = re.sub(r"\s+", " ", str(getattr(chunk, "text", "") or "")).strip()[:snippet_chars]
        chapter = str(getattr(chunk, "chapter", "") or "")
        hits.append(
            {
                "title": title or format_book_title(Path(rel).name),
                "path": rel,
                "chapter": chapter,
                "snippet": snippet,
                "score": round(score, 3),
            }
        )
        if len(hits) >= limit:
            return hits

    library_root = root if root is not None else find_nexus_root()
    if library_root is None:
        return hits
    for book in scan_library(library_root):
        title = str(book.get("title") or "")
        if not any(word in title.lower() for word in words):
            continue
        formats = book.get("formats")
        path = ""
        if isinstance(formats, list) and formats:
            path = str(formats[0].get("path") or "")
        if path in seen:
            continue
        seen.add(path)
        hits.append(
            {
                "title": title,
                "path": path,
                "chapter": "",
                "snippet": "The title matches what you asked.",
                "score": 0,
            }
        )
        if len(hits) >= limit:
            break
    return hits


def books_for_query(
    query: str,
    *,
    limit: int = 3,
    root: Path | None = None,
    searcher: object | None = None,
    summary_root: Path | None = None,
) -> str:
    """Prompt block with saved summaries and passages from the Nexus shelf."""
    from .nexus_summaries import load_summary

    hits = suggest_books(query, limit=limit, root=root, searcher=searcher, snippet_chars=700)
    if not hits:
        return ""
    lines = ["Knowledge Nexus shelf. Cite a title and chapter only from this list:"]
    for hit in hits:
        title = hit["title"]
        path = str(hit["path"] or "")
        chapter = str(hit.get("chapter") or "")
        snippet = str(hit.get("snippet") or "")
        where = f", {chapter}" if chapter else ""
        lines.append(f"- {title}{where} [{path}]")
        summary = load_summary(path, root=summary_root) if path else ""
        if summary:
            lines.append(f"  Summary: {summary}")
        if snippet and snippet != summary:
            lines.append(f"  Passage: {snippet}")
    return "\n".join(lines)


def sync_icloud_library(*, apply: bool = False, timeout_s: int = 180) -> dict[str, object]:
    """Copy new books from iCloud Information into the local Nexus mirror."""
    source = find_icloud_source()
    if source is None:
        return {
            "ok": False,
            "apply": apply,
            "copied": [],
            "errors": ["iCloud Information library was not found"],
        }
    destination = mirror_dir()
    if apply:
        destination.mkdir(parents=True, exist_ok=True)
    return sync_tree(source, destination, apply=apply, timeout_s=timeout_s)
