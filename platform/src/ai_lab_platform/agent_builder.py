"""Conversational agent draft. The operator describes the job. The lab picks the model."""

from __future__ import annotations

import json
import re
from typing import Any, Callable

from .tool_catalog import access_for

_OPENING = "What do you want done?"
_FOLLOW = "What should it hand you when it is finished?"
_STEPS = "List the steps in the order they should happen."
_WHICH = "Should it follow the same steps every time, or decide as it goes?"
_WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{1,40}")
_STEP_SPLIT = re.compile(r"\s+(?:and then|then|next|finally)\s+", re.IGNORECASE)
_STEP_MARK = re.compile(r"^\s*(?:\d+[\).\]]|[-*])\s*")

_CODING = ("code", "repo", "patch", "implement", "function", "bug", "refactor", "git", "python", "script")
_LEARN = ("teach", "learn", "explain", "tutor", "lesson", "study")
_PRODUCT = ("spec", "product", "roadmap", "feature", "decision")
_COMPANY = ("company", "weekly", "brief", "invoice", "mail", "customer")
_LAB = ("lab", "health", "status", "disk", "scheduler")
_SECURITY = ("security", "malware", "hypervisor", "vm", "vise", "isolation", "quarantine")
_FAST = ("fast", "quick", "short")
_DONE = (
    "everything is good",
    "looks good",
    "build it",
    "create it",
    "go ahead",
    "that's enough",
    "that is enough",
    "that's good",
    "that is good",
    "save it",
)
_FLOW = ("then", "first", "next", "finally", "step", "every morning", "every day", "in order", "each time", "routine", "checklist", "always")
_JUDGMENT = ("decide", "figure out", "research", "unsure", "judgment", "reason", "explore", "investigate", "whatever makes sense")
_MISSING = (
    ("email", "mail"),
    ("inbox", "mail"),
    ("mail", "mail"),
    ("portfolio", "a portfolio reader"),
    ("slack", "Slack"),
    ("jira", "a ticket system"),
    ("ticket", "a ticket system"),
    ("calendar", "a calendar"),
)


def interviewer_model(installed: list[str]) -> str:
    """The conversation that drafts an agent uses the general local model, not the fast one."""
    for name in ("qwen3.6:35b-a3b", "qwen3.8:27b", "llama3.2:3b"):
        if name in installed:
            return name
    if installed:
        return installed[0]
    return "qwen3.6:35b-a3b"


def opening_question() -> str:
    return _OPENING


def choose_model(
    purpose: str,
    text: str,
    installed: list[str],
    roles: dict[str, str] | None = None,
) -> tuple[str, str, str]:
    """Return backend, tag, and a sentence. Never a billed model, and never a temperature."""
    installed_set = {name for name in installed if name}
    assigned = roles or {}
    blob = (text or "").lower()

    def take(role_id: str, fallbacks: tuple[str, ...], sentence: str) -> tuple[str, str, str] | None:
        preferred = str(assigned.get(role_id) or "").strip()
        options = ([preferred] if preferred else []) + list(fallbacks)
        for name in options:
            if name in installed_set:
                return "ollama", name, sentence
        return None

    if any(word in blob for word in _FAST):
        picked = take("fast-local", ("llama3.2:3b",), "I'll use the fast local model for this.")
        if picked:
            return picked
    if purpose == "build":
        picked = take(
            "coding-local",
            ("qwen3-coder:30b", "qwen3.6:35b-a3b"),
            "I'll use the coding model for this.",
        )
        if picked:
            return picked
    picked = take(
        "general-local",
        ("qwen3.6:35b-a3b", "qwen3.8:27b", "llama3.2:3b"),
        "I'll use the general local model for this.",
    )
    if picked:
        return picked
    if installed:
        return "ollama", installed[0], "I'll use the local model that is installed."
    return "ollama", "qwen3.6:35b-a3b", "I'll use the general local model for this."


def classify_purpose(text: str) -> tuple[str, str]:
    blob = (text or "").lower()
    if any(word in blob for word in _CODING):
        return "build", "coding-assistant"
    if any(word in blob for word in _SECURITY):
        return "security", "security"
    if any(word in blob for word in _LEARN):
        return "learn", "research"
    if any(word in blob for word in _COMPANY):
        return "company", "research"
    if any(word in blob for word in _LAB) and not any(word in blob for word in _CODING):
        return "lab", "lab-operations"
    if any(word in blob for word in _PRODUCT):
        return "product", "research"
    return "learn", "research"


def _user_turns(messages: list[dict[str, Any]]) -> list[str]:
    out: list[str] = []
    for row in messages:
        if not isinstance(row, dict):
            continue
        if str(row.get("role") or "") != "user":
            continue
        text = str(row.get("content") or "").strip()
        if text:
            out.append(text[:2000])
    return out


def _title_from(text: str) -> str:
    words = _WORD.findall(text)[:6]
    if not words:
        return "New agent"
    title = " ".join(words)
    return title[:80]


def external_account(text: str) -> str | None:
    """A job that needs an account the lab does not have. The repository is not that account."""
    blob = (text or "").lower()
    if any(word in blob for word in ("gmail", "inbox", "e-mail", "email", "mailbox", "mail")):
        return "mail"
    for word, label in _MISSING:
        if word in blob:
            return label
    return None


def _agreed_to_server(messages_text: str) -> bool:
    lines = [line.strip().lower() for line in (messages_text or "").splitlines() if line.strip()]
    if len(lines) < 2:
        return False
    later = "\n".join(lines[1:])
    return any(phrase in later for phrase in ("yes", "add it", "install", "use it", "use the server", "connect"))


def _gap_question(text: str) -> str:
    if external_account(text) == "mail":
        return (
            "Google publishes a Gmail MCP server. I can add it for this agent. "
            "It stays off until you authorize it, and the sign-in stays with Google. "
            "Should I add it?"
        )
    label = external_account(text) or "that system"
    return (
        "The lab does not have "
        + label
        + ". The AI Lab repository is the lab's own code, not that account. "
        + "How should it reach it, or should this wait?"
    )


def _steps_from(text: str) -> list[str]:
    raw_text = text or ""
    sequenced = _STEP_SPLIT.search(raw_text) is not None
    chunks: list[str] = []
    for line in raw_text.splitlines():
        if _STEP_MARK.search(line):
            sequenced = True
        cleaned = _STEP_MARK.sub("", line).strip()
        if not cleaned:
            continue
        parts = _STEP_SPLIT.split(cleaned)
        for part in parts:
            step = part.strip(" .")
            if step:
                chunks.append(step[:240])
    if not sequenced:
        return []
    return chunks[:12]


def classify_shape(text: str) -> str | None:
    """workflow when the steps are already known. agent when the job needs a decision. None when both are present."""
    blob = (text or "").lower()
    steps = _steps_from(text)
    ordered = len(steps) >= 2 or any(word in blob for word in _FLOW)
    judgment = any(word in blob for word in _JUDGMENT)
    if ordered and judgment:
        return None
    if ordered:
        return "workflow"
    return "agent"


def _gaps_for(text: str) -> list[str]:
    blob = (text or "").lower()
    missing: list[str] = []
    for word, label in _MISSING:
        if word in blob and label not in missing:
            missing.append(label)
    return missing


def _draft_from_text(text: str, installed: list[str], roles: dict[str, str] | None) -> dict[str, Any]:
    purpose, agent = classify_purpose(text)
    shape = classify_shape(text) or "agent"
    steps = _steps_from(text) if shape == "workflow" else []
    account = external_account(text)
    backend, model, note = choose_model(purpose, text, installed, roles)
    instructions = text.strip()[:4000]
    if account:
        instructions = (
            instructions
            + "\n\nThe AI Lab repository is the lab's own code and notes. It is not the account. "
            + "Do not cite a work order as access. Only one local model is loaded at a time."
        )
    read_tools = ["search_threads", "get_thread", "list_labels", "list_drafts"] if account == "mail" else []
    access = access_for(text, purpose, shape=shape)
    skills = ["Draft a reply"] if account == "mail" else list(access["skills"])
    if account == "mail":
        note = (
            "This uses the chat model. The coding model stays unloaded. "
            "The Gmail server, the Draft a reply skill, and the read tools are registered. "
            "The server stays off until you sign in with Google. Sending and labels wait for approval."
        )
        if shape == "workflow":
            model = ""
            backend = ""
    elif account:
        note = (
            "This uses the chat model. The coding model stays unloaded, because only one of them can be loaded. "
            "The account is not connected. The AI Lab repository is not that account."
        )
        if shape == "workflow":
            model = ""
            backend = ""
    elif shape == "workflow":
        note = "This is a workflow. The steps stay in order. The lab does not pick a model to decide the sequence."
        model = ""
        backend = ""
    offers = ["gmail"] if account == "mail" else list(access["mcp_offers"])
    if offers and account != "mail":
        note = (
            note
            + " Registered "
            + ", ".join(offers)
            + ". Those servers stay off until you authorize them. Their read tools are saved with this agent."
        )
    if purpose == "build" and shape != "workflow":
        note = note + " Repo reads are attached. Edits wait for approval."
    tools = read_tools if account == "mail" else ([] if account else list(access["tools"]))
    mcp_tools = read_tools if account == "mail" else list(access["mcp_tools"])
    return {
        "title": _title_from(text),
        "purpose": purpose,
        "agent": agent,
        "kind": shape,
        "steps": steps,
        "instructions": instructions,
        "knowledge": "",
        "tools": tools,
        "mcp_tools": mcp_tools,
        "skills": skills,
        "backend": backend,
        "model": model,
        "model_note": note,
        "mcp_offer": "gmail" if account == "mail" else "",
        "mcp_offers": offers,
    }


def _json_object(text: str) -> dict[str, Any] | None:
    raw = text or ""
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        body = json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return None
    return body if isinstance(body, dict) else None


def _clean_question(text: str) -> str:
    question = " ".join(str(text or "").split())
    lower = question.lower()
    if not question or any(word in lower for word in ("temperature", "quant", "provider", "backend", "model id")):
        return _FOLLOW
    return question[:400]


def _ready_to_build(text: str) -> bool:
    blob = " ".join((text or "").lower().split())
    return any(phrase in blob for phrase in _DONE)


def _asked(messages: list[dict[str, Any]]) -> list[str]:
    out: list[str] = []
    for row in messages:
        if isinstance(row, dict) and str(row.get("role") or "") == "assistant":
            text = str(row.get("content") or "").strip()
            if text:
                out.append(text)
    return out


def _question_queue(text: str) -> list[str]:
    items: list[str] = []
    if external_account(text):
        items.append(_gap_question(text))
        items.append("What should it hand you when it is finished? It still cannot open that account.")
    shape = classify_shape(text)
    if shape is None:
        items.append(_WHICH)
    if shape == "workflow" and len(_steps_from(text)) < 2:
        items.append(_STEPS)
    elif shape == "workflow":
        items.append("I'll keep those steps in order. What step is missing, if any?")
    items.extend(
        [
            _FOLLOW,
            "How often should it run? Only when you start it, or on a schedule?",
            "What must it stop and ask you before doing?",
            "What should it leave alone?",
            "Who else is this for?",
            "What does a bad result look like?",
            "Tell me anything else that matters, or say build it.",
        ]
    )
    seen: list[str] = []
    for item in items:
        if item not in seen:
            seen.append(item)
    return seen


def interview(
    messages: list[dict[str, Any]],
    *,
    installed: list[str],
    roles: dict[str, str] | None = None,
    complete: Callable[[str], str] | None = None,
) -> dict[str, Any]:
    """Keep asking until the operator says to build. The lab still picks the model."""
    del complete  # questions are a checklist so a second model is not loaded
    users = _user_turns(messages)
    if not users:
        return {"ready": False, "question": _OPENING, "draft": None}
    joined = "\n".join(users)
    if _ready_to_build(users[-1]):
        return {"ready": True, "question": "", "draft": _draft_from_text(joined, installed, roles)}
    asked = _asked(messages)
    for question in _question_queue(joined):
        if question not in asked:
            return {"ready": False, "question": question, "draft": None}
    return {"ready": False, "question": "Say build it when this is enough.", "draft": None}
