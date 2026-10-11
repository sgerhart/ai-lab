"""File a finished day's personal-agent chats into the memory vault.

The answering model does not call this. The scheduler tick does, for days
that are already over. People, preferences, and decisions are not edited.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Protocol

from .conversation import Conversation, Message, MessageRole
from .memory_vault import MemoryVault

_LOOKBACK_DAYS = 7
_LINE_CAP = 180
_FILED_KEEP = 30


class ChatSource(Protocol):
    def list_conversations(self, *, limit: int = 50) -> list[Conversation]: ...

    def list_messages(self, conversation_id: str) -> list[Message]: ...


def utc_day_of(stamp: str) -> str:
    text = (stamp or "").strip()
    if len(text) < 10 or text[4] != "-" or text[7] != "-":
        return ""
    day = text[:10]
    if len(text) > 10 and text[10] not in "Tt ":
        return ""
    try:
        datetime.strptime(day, "%Y-%m-%d")
    except ValueError:
        return ""
    return day


def elapsed_days(when: datetime, *, lookback: int = _LOOKBACK_DAYS) -> list[str]:
    """UTC dates before `when`, oldest first. Today is not included."""
    moment = when if when.tzinfo is not None else when.replace(tzinfo=timezone.utc)
    today = moment.astimezone(timezone.utc).date()
    span = max(1, min(int(lookback), _LOOKBACK_DAYS))
    return [(today - timedelta(days=offset)).isoformat() for offset in range(span, 0, -1)]


def _snippet(text: str) -> str:
    return " ".join((text or "").split())[:_LINE_CAP]


def chat_lines(store: ChatSource, day: str, *, already: str = "") -> list[str]:
    """User and assistant lines from personal chats on `day`. Other agents are skipped."""
    lines: list[str] = []
    conversations = list(store.list_conversations(limit=200))
    conversations.reverse()
    for conversation in conversations:
        if conversation.agent != "personal":
            continue
        marker = f"chat:{conversation.id}"
        if marker in already:
            continue
        titled = False
        for message in store.list_messages(conversation.id):
            if message.role not in {MessageRole.USER, MessageRole.ASSISTANT}:
                continue
            if utc_day_of(message.created_at) != day:
                continue
            snippet = _snippet(message.content)
            if not snippet:
                continue
            if not titled:
                title = _snippet(conversation.title) or "untitled"
                lines.append(f"{marker} {title}")
                titled = True
            lines.append(f"{marker} {message.role.value}: {snippet}")
            if len(lines) >= 40:
                return lines
    return lines


def file_personal_day(store: ChatSource, vault: MemoryVault, day: str) -> dict[str, Any]:
    """Append that day's personal chats. No-op when there is nothing new."""
    existing = ""
    path = vault.root / "timeline" / "daily" / f"{day}.md"
    if path.is_file() and not path.is_symlink():
        try:
            existing = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            existing = ""
    lines = chat_lines(store, day, already=existing)
    if not lines:
        return {"ok": True, "day": day, "wrote": False, "lines": 0}
    rel = vault.record_day(day, lines)
    return {"ok": True, "day": day, "wrote": True, "lines": len(lines), "path": rel}


def file_elapsed_personal_days(
    store: ChatSource,
    vault: MemoryVault,
    *,
    when: datetime,
    filed_days: list[str],
) -> dict[str, Any]:
    """File each finished UTC day in the lookback window once."""
    filed = [day for day in filed_days if utc_day_of(day) == day]
    wrote: list[str] = []
    for day in elapsed_days(when):
        if day in filed:
            continue
        result = file_personal_day(store, vault, day)
        filed.append(day)
        if result.get("wrote"):
            wrote.append(day)
    return {
        "ok": True,
        "wrote": wrote,
        "filed_days": filed[-_FILED_KEEP:],
    }
