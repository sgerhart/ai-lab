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
