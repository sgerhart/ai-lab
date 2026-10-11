"""A read-only review of one Antares lead.

Antares names a file. This step asks a coding model which line matches, and
keeps the answer to a verdict, a line number, and one sentence. It does not
describe an attack or change the file.
"""

from __future__ import annotations

import json
import re
from typing import Any

_VERDICTS = {"confirmed", "rejected", "uncertain"}
_ATTACK = re.compile(r"\b(exploit|payload|pwn|reverse shell|proof of concept)\b", re.I)


def numbered_excerpt(text: str, *, limit: int = 160) -> tuple[str, int]:
    lines = text.splitlines()
    shown = lines[:limit]
    body = "\n".join(f"{index}|{line[:160]}" for index, line in enumerate(shown, 1))
    if len(lines) > limit:
        body += f"\n… {len(lines) - limit} more lines were not sent."
    return body, len(lines)


def review_prompt(*, path: str, cwe: str, title: str, excerpt: str) -> str:
    return (
        "You review source that Antares flagged. Reply with one JSON object and no other text.\n"
        '{"verdict":"confirmed"|"rejected"|"uncertain","line":null,"reason":"one sentence"}\n'
        "Use line only when that numbered line is why the class fits or does not fit. "
        "Describe the code. Do not describe an attack, a command, or a payload.\n"
        f"File: {path}\nClass: {cwe or 'unspecified'}\nTitle: {title or 'Untitled'}\n"
        f"Source:\n{excerpt}\n"
    )


def parse_review(raw: str, *, line_count: int) -> dict[str, Any]:
    """Accept a model reply only when the line is inside the file."""
    text = (raw or "").strip()
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return _uncertain("The reviewer did not return a finding.")
    try:
        body = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return _uncertain("The reviewer did not return a finding.")
    if not isinstance(body, dict):
        return _uncertain("The reviewer did not return a finding.")
    verdict = str(body.get("verdict") or "").strip().lower()
    if verdict not in _VERDICTS:
        verdict = "uncertain"
    line = _line_number(body.get("line"), line_count)
    reason = " ".join(str(body.get("reason") or "").split())[:240]
    if not reason or _ATTACK.search(reason):
        return _uncertain("The review was kept only as a file lead.")
    if verdict in {"confirmed", "rejected"} and line is None:
        verdict = "uncertain"
        reason = "The reviewer did not name a line in the file."
    return {"verdict": verdict, "line": line, "reason": reason}


def _line_number(value: Any, line_count: int) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, str) and value.strip().isdigit():
        value = int(value.strip())
    if not isinstance(value, int):
        return None
    if value < 1 or value > max(line_count, 0):
        return None
    return value


def _uncertain(reason: str) -> dict[str, Any]:
    return {"verdict": "uncertain", "line": None, "reason": reason}
