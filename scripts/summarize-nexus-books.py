#!/usr/bin/env python3
"""Write one summary per Nexus book, paper, or course.

Dry-run unless --apply. A file that already has a summary for the same size
and modification time is skipped. The model call goes to the lab Ollama URL
already used by the control plane.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.nexus_library import BOOK_SUFFIXES, CONTENT_DIRS, find_nexus_root  # noqa: E402
from ai_lab_platform.nexus_study import format_book_title  # noqa: E402
from ai_lab_platform.nexus_summaries import (  # noqa: E402
    opening_text,
    save_summary,
    summary_from_excerpt,
    summary_is_current,
)
from ai_lab_platform.ollama_backend import require_lab_ollama_url  # noqa: E402


def _complete(url: str, model: str, title: str, excerpt: str) -> str:
    require_lab_ollama_url(url)
    prompt = (
        "Write two or three sentences for a personal library card. "
        "Say what this work is about and who it helps. "
        "Use only the excerpt. Do not invent a chapter, finding, or edition.\n\n"
        f"Title: {title}\nExcerpt: {excerpt}"
    )
    body = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": 180, "temperature": 0.2},
        }
    ).encode("utf-8")
    request = Request(
        f"{url.rstrip('/')}/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=120) as response:  # noqa: S310
        payload = json.loads(response.read().decode("utf-8"))
    return str(payload.get("response") or "")


def _documents(root: Path) -> list[tuple[str, Path]]:
    found: list[tuple[str, Path]] = []
    seen: set[str] = set()
    ordered: list[Path] = []
    for folder in CONTENT_DIRS:
        base = root / folder
        if base.is_dir():
            ordered.extend(base.rglob("*.epub"))
    for folder in CONTENT_DIRS:
        base = root / folder
        if base.is_dir():
            ordered.extend(base.rglob("*.pdf"))
    for path in ordered:
        if path.suffix.lower() not in BOOK_SUFFIXES:
            continue
        rel = path.relative_to(root).as_posix()
        if any(part.startswith(".") for part in Path(rel).parts):
            continue
        stem = f"{path.parent}/{path.stem}"
        if stem in seen:
            continue
        seen.add(stem)
        found.append((rel, path))
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize the Nexus shelf once per file")
    parser.add_argument("--apply", action="store_true", help="Write summaries. Default is a dry run.")
    parser.add_argument("--model", default=os.environ.get("AI_LAB_SUMMARY_MODEL", "").strip())
    parser.add_argument("--url", default=os.environ.get("STUDIO_OLLAMA_URL", "").strip())
    parser.add_argument("--limit", type=int, default=0, help="Stop after this many new summaries. 0 means all.")
    args = parser.parse_args()
    root = find_nexus_root()
    if root is None:
        print("Nexus library was not found.", file=sys.stderr)
        return 1
    docs = _documents(root)
    pending = [(rel, path) for rel, path in docs if not summary_is_current(rel, path)]
    print(f"{len(docs)} items, {len(pending)} need a summary. apply={args.apply}")
    if not args.apply:
        for rel, _path in pending[:20]:
            print(rel)
        if len(pending) > 20:
            print(f"... {len(pending) - 20} more")
        return 0
    if not args.url or not args.model:
        print("Set STUDIO_OLLAMA_URL and --model, or AI_LAB_SUMMARY_MODEL.", file=sys.stderr)
        return 2
    written = 0
    for rel, path in pending:
        if args.limit and written >= args.limit:
            break
        title = format_book_title(path.name)
        excerpt = opening_text(path, rel)
        def complete(_title: str, body: str) -> str:
            return _complete(args.url, args.model, _title, body)

        try:
            summary = summary_from_excerpt(title, excerpt, complete)
        except Exception as exc:  # noqa: BLE001
            print(f"skip {rel}: {exc}", file=sys.stderr)
            continue
        if not summary:
            print(f"skip {rel}: not enough text", file=sys.stderr)
            continue
        save_summary(rel, path, summary, title=title)
        written += 1
        print(f"saved {title}")
    print(f"wrote {written}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
