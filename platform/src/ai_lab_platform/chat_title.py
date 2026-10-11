"""Short conversation titles from the model that just answered."""

from __future__ import annotations

import re

from .model_router import CompletionRequest, ModelRouter

_GENERIC = {"", "chat", "ui", "new chat", "untitled"}
_TITLE_RE = re.compile(r"^[^\r\n]{1,48}$")


def title_is_generic(title: str) -> bool:
    return (title or "").strip().lower() in _GENERIC


def clean_model_title(text: str) -> str:
    """Keep a single short name. Drop quotes, labels, and model scaffolding."""
    raw = (text or "").strip()
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    if not raw:
        return ""
    line = raw.splitlines()[0].strip()
    line = re.sub(r"^(title\s*:\s*)", "", line, flags=re.IGNORECASE)
    line = line.strip("\"'`“”").strip().rstrip(".")
    line = re.sub(r"\s+", " ", line)
    if line.lower() in _GENERIC or line.startswith("["):
        return ""
    if len(line) > 48:
        line = line[:48].rstrip()
    if not _TITLE_RE.match(line):
        return ""
    return line


def derive_descriptive_title(text: str) -> str:
    """Extract a concise, descriptive title from a prompt or objective without LLM overhead."""
    raw = (text or "").strip()
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    if not raw:
        return ""
    raw = re.sub(r"^#+\s*", "", raw)
    first_line = raw.splitlines()[0].strip()
    first_line = re.sub(r"^[\-\*\d\.\)\s]+", "", first_line).strip()
    if not first_line:
        return ""

    patterns = [
        r"^(can\s+you\s+(please\s+)?(help\s+me\s+)?(create|make|build|write|draft|generate|give\s+me)\s+(a|an|the)?\s*)",
        r"^(please\s+(create|make|build|write|draft|generate|give\s+me|summarize|explain)\s+(a|an|the)?\s*)",
        r"^(i\s+want\s+(to\s+)?(create|make|build|write|see|have)\s+(a|an|the)?\s*)",
        r"^(could\s+you\s+(please\s+)?(create|make|build|write|generate)\s+(a|an|the)?\s*)",
        r"^(how\s+(can\s+we|do\s+i|to)\s*)",
        r"^(tell\s+me\s+about\s*)",
        r"^(can\s+we\s+(also\s+)?(use|make|build|do)\s*)",
        r"^(can\s+you\s+(also\s+)?(provide|format|fix|add)\s*)",
    ]
    cleaned = first_line
    for pat in patterns:
        cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE).strip()

    cleaned = cleaned.strip("\"'`“”").rstrip(".?!:;,")
    if not cleaned:
        cleaned = first_line[:40].strip()

    if cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:]

    if len(cleaned) > 46:
        cutoff = cleaned[:46].rfind(" ")
        if cutoff > 20:
            cleaned = cleaned[:cutoff].rstrip()
        else:
            cleaned = cleaned[:46].rstrip()

    return cleaned if cleaned.lower() not in _GENERIC else ""


def propose_chat_title(
    router: ModelRouter,
    *,
    backend: str,
    model: str,
    user_text: str,
    assistant_text: str,
) -> str:
    """Ask the same backend for a topic name. Returns '' if it does not."""
    prompt = (
        "Name this conversation in 2 to 6 words.\n"
        "Use the topic. Do not say Chat or Untitled.\n"
        "Reply with the name only.\n\n"
        f"User: {(user_text or '')[:400]}\n"
        f"Assistant: {(assistant_text or '')[:400]}"
    )
    try:
        response = router.complete(
            CompletionRequest(
                model=model or "fake-instruct",
                prompt=prompt,
                backend=backend or "fake",
                system="You write short conversation titles.",
            )
        )
    except Exception:
        return ""
    return clean_model_title(response.text)

