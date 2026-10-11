"""Official CWE names and short definitions. Names are copied from MITRE; see data/CWE_NOTICE.txt."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

STANDS_FOR = "Common Weakness Enumeration"
UNKNOWN = "No standard name is recorded for this class."
_DATA = Path(__file__).resolve().parent / "data" / "cwe_classes.json"


@lru_cache(maxsize=1)
def _catalog() -> dict[str, dict[str, str]]:
    loaded = json.loads(_DATA.read_text(encoding="utf-8"))
    rows = loaded.get("classes") if isinstance(loaded, dict) else None
    by_id: dict[str, dict[str, str]] = {}
    if not isinstance(rows, list):
        return by_id
    for row in rows:
        if not isinstance(row, dict):
            continue
        ident = str(row.get("id") or "").strip().upper()
        name = " ".join(str(row.get("name") or "").split())
        meaning = " ".join(str(row.get("meaning") or "").split())
        if not ident or not name:
            continue
        by_id[ident] = {"id": ident, "name": name, "meaning": meaning}
    return by_id


def normalize_cwe(raw: str) -> str:
    text = " ".join((raw or "").split()).upper()
    if text.isdigit():
        return f"CWE-{text}"
    return text


def explain(raw: str) -> dict[str, str]:
    """One class id, its MITRE name, and the short definition."""
    ident = normalize_cwe(raw)
    row = _catalog().get(ident)
    if row is None:
        return {"id": ident, "name": "", "meaning": UNKNOWN}
    return dict(row)


def catalog_payload() -> dict[str, object]:
    loaded = json.loads(_DATA.read_text(encoding="utf-8"))
    version = loaded.get("version") if isinstance(loaded, dict) else ""
    return {
        "stands_for": STANDS_FOR,
        "version": str(version or ""),
        "source_url": "https://cwe.mitre.org/",
        "classes": _catalog(),
    }
