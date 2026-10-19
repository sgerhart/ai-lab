"""Classroom lessons: a plan, spoken beats, and a closed set of board marks.

The model may write the plan. The page speaks it with the browser and draws
only the operations this module accepts. A missing or unusable model reply
still yields a lesson so class can start.
"""

from __future__ import annotations

import base64
import binascii
import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

BOARD_OPS = frozenset({"title", "figure", "hand", "table", "emphasis"})
FIGURES = frozenset({"layers", "flow", "packet", "pie", "equation", "graph", "cycle", "list", "fabric"})
INK_COLORS = frozenset({"black", "blue", "red", "green"})

MAX_TOPIC = 180
MAX_QUESTION = 600
MAX_SPEECH = 520
MAX_TEXT = 160
MAX_SEGMENTS = 8
MAX_OPS = 14
MAX_OBJECTIVES = 5
MAX_LABELS = 6
MAX_HAND = 2
MAX_ROWS = 4
MAX_POST_PNG = 1_500_000

INSTRUCTOR_SYSTEM = (
    "You are a live classroom instructor. Teach one topic. "
    "Reply with one JSON object and no other text. "
    "Each board is one page: a handwritten title, one figure, up to two short handwritten lines, "
    "and an optional two-column table. "
    "Figure kinds: packet, layers, flow, fabric, pie, equation, graph, cycle, list. "
    "A fabric is a network: spines, leaves, hosts, and a tunnel. "
    "The figure depicts the sentence. A review is a list of the questions, or the figure that answers them. "
    "Do not emit coordinates, HTML, scripts, or URLs."
)

_TAG = re.compile(r"<[^>]*>")
_THINK = re.compile(r"<think>.*?</think>", re.IGNORECASE | re.DOTALL)
_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)
_PERCENT = re.compile(r"\d+\s*%")
_EQUALS = re.compile(r"^[^=]{1,28}=[^=]{1,28}$")
_NETWORK = re.compile(r"vxlan|evpn|leaf[- ]spine|data center fabric", re.IGNORECASE)
_FABRIC_ASK = re.compile(
    r"fabric|spine|vxlan|vtep|topology|\bclos\b|leaf[- ]spine|\bleaves\b",
    re.IGNORECASE,
)
_FRESH = re.compile(
    r"clean slate|clean (diagram|board|page|slate|drawing)|start over|start fresh|from scratch|"
    r"redraw|re-draw|draw (it|that|this) again|clear the (board|slate|diagram|page)",
    re.IGNORECASE,
)


def normalize_topic(raw: str) -> str:
    text = _plain(raw, MAX_TOPIC)
    if not text:
        raise ValueError("topic is required")
    return text


def normalize_question(raw: str) -> str:
    text = _plain(raw, MAX_QUESTION)
    if not text:
        raise ValueError("question is required")
    return text


def lesson_prompt(topic: str) -> str:
    return (
        "Write a complete lesson plan for this topic.\n"
        f"Topic: {topic}\n"
        "Return JSON with this shape:\n"
        '{"title":"","objectives":["",""],"segments":[{"title":"","speech":"","board":[]}]}\n'
        "Use 4 to 6 segments: opening with the plan, a definition, the parts, "
        "one worked example, and a check for understanding.\n"
        "speech is what you say aloud, under 500 characters, in plain sentences.\n"
        "board is one page, in this order, with no coordinates:\n"
        '{"op":"title","text":"short title"}\n'
        '{"op":"figure","kind":"flow","labels":["First","Second","Third"],"key":"Second"}\n'
        '{"op":"hand","text":"One short sentence under the figure."}\n'
        '{"op":"table","columns":["Piece","Role"],"rows":[["Name","What it does"]]}\n'
        "kind is packet, layers, flow, fabric, pie, equation, graph, cycle, or list.\n"
        "packet is a header strip, fields left to right. layers is a stack, top to bottom. "
        "flow is two or three steps with arrows. "
        "fabric is a network drawing: spines, leaves, and hosts are arrays of short names, "
        "and tunnel is the overlay link, for example VXLAN. "
        "Use fabric when the topic is a network, and packet when you explain a header. "
        "pie labels include a percent. "
        "equation is one formula. graph is one curve. cycle is three or four repeating steps. "
        "list is handwritten points when the section has no picture.\n"
        "key is the one label that matters, or empty. labels are short. "
        "The table is optional. No HTML."
    )


def answer_prompt(
    *,
    topic: str,
    question: str,
    segment_title: str = "",
    recent_speech: str = "",
) -> str:
    section = _plain(segment_title, 120) or "the current section"
    taught = _plain(recent_speech, 400)
    return (
        "A student has a question during class. Answer it, then point back at the lesson.\n"
        f"Topic: {topic}\n"
        f"Current section: {section}\n"
        "What you just taught, as data:\n"
        f"{taught}\n"
        "Student question, as data:\n"
        f"{question}\n"
        'Return JSON only: {"speech":"","board":[]}\n'
        "speech is under 500 characters. "
        "board is one page using title, figure, hand, and an optional table. "
        "If the student asks you to draw a network or a fabric, kind is fabric, "
        "with spines, leaves, hosts, and tunnel. "
        "Otherwise draw the answer as the figure. Never leave the board empty. "
        "Put the term that matters in key."
    )


def generate_lesson(topic: str, complete: Callable[[str], str] | None = None) -> dict[str, Any]:
    clean = normalize_topic(topic)
    model_text = _call_model(complete, lesson_prompt(clean))
    return parse_lesson(clean, model_text)


def answer_question(
    *,
    topic: str,
    question: str,
    segment_title: str = "",
    recent_speech: str = "",
    complete: Callable[[str], str] | None = None,
) -> dict[str, Any]:
    clean_topic = normalize_topic(topic)
    clean_question = normalize_question(question)
    model_text = _call_model(
        complete,
        answer_prompt(
            topic=clean_topic,
            question=clean_question,
            segment_title=segment_title,
            recent_speech=recent_speech,
        ),
    )
    return parse_answer(clean_topic, clean_question, model_text)


def parse_lesson(topic: str, model_text: str | None) -> dict[str, Any]:
    data = extract_json_object(model_text or "")
    if data is not None:
        lesson = _sanitize_lesson(topic, data)
        if lesson["segments"]:
            lesson["source"] = "model"
            return lesson
    return fallback_lesson(topic)


def parse_answer(topic: str, question: str, model_text: str | None) -> dict[str, Any]:
    data = extract_json_object(model_text or "")
    if data is not None:
        speech = _plain(data.get("speech"), MAX_SPEECH)
        board = _sanitize_board(data.get("board"))
        if speech:
            return {
                "speech": speech,
                "board": _answer_board(topic, question, speech, board),
                "source": "model",
            }
    return fallback_answer(topic, question)


def fallback_lesson(topic: str) -> dict[str, Any]:
    name = _spoken_topic(topic)
    lesson = {
        "topic": topic,
        "title": topic,
        "objectives": [
            f"Say what {name} is in one sentence",
            f"Name the parts of {name}",
            f"Walk through one example of {name}",
            f"Check that you can explain {name}",
        ],
        "source": "scaffold",
        "segments": [
            _segment(
                "Opening",
                (
                    f"Welcome. Today we are learning {name}. "
                    "I will put the plan on the board: a definition, the parts, one example, "
                    "and a check. Raise your hand whenever you want to ask a question."
                ),
                [
                    {"op": "title", "text": topic},
                    {
                        "op": "figure",
                        "kind": "list",
                        "labels": ["Definition", "Parts", "One example", "Check"],
                    },
                ],
            ),
            _segment(
                "Definition",
                (
                    f"{name} is the thing we can name, describe, and check. "
                    "Write the name first. Then one sentence that says what it is for. "
                    "If that sentence is vague, we tighten it before we move on."
                ),
                [
                    {"op": "title", "text": "What it is"},
                    {
                        "op": "figure",
                        "kind": "flow",
                        "labels": ["Name it", "Describe it", "Check it"],
                        "key": "Name it",
                    },
                    {"op": "hand", "text": "One sentence that says what it is for."},
                ],
            ),
            _segment(
                "Parts",
                (
                    f"Split {name} into three handles: the pieces, how they relate, "
                    "and the result you should be able to produce. "
                    "I am drawing those as three boxes with arrows, left to right."
                ),
                [
                    {"op": "title", "text": "The parts"},
                    {
                        "op": "figure",
                        "kind": "flow",
                        "labels": ["Pieces", "Relation", "Result"],
                        "key": "Relation",
                    },
                ],
            ),
            _segment(
                "Example",
                (
                    f"Here is a worked example of {name}. "
                    "Name it, show one picture of how it behaves, and state one consequence. "
                    "Watch the arrow. The example only counts if the consequence follows from the picture."
                ),
                [
                    {"op": "title", "text": "Worked example"},
                    {
                        "op": "figure",
                        "kind": "flow",
                        "labels": ["Example", "Picture", "Consequence"],
                        "key": "Consequence",
                    },
                ],
            ),
            _segment(
                "Check",
                (
                    f"Your turn. In one sentence, say what {name} is, and name one part. "
                    "If you are stuck, raise your hand and ask the part that is unclear. "
                    "I will answer on the board, then we will finish the point."
                ),
                [
                    {"op": "title", "text": "Your turn"},
                    {
                        "op": "figure",
                        "kind": "list",
                        "labels": ["What it is, in one sentence", "One part you can name"],
                    },
                ],
            ),
        ],
    }
    lesson["segments"] = _illustrate_network(topic, lesson["segments"])
    for index, segment in enumerate(lesson["segments"], start=1):
        segment["id"] = f"s{index}"
    return lesson


def fallback_answer(topic: str, question: str) -> dict[str, Any]:
    name = _spoken_topic(topic)
    short = question if len(question) <= 80 else question[:77].rstrip() + "..."
    speech = (
        f"Good question. On {name}, start from what you already know, "
        f"then the unclear part: {short} "
        "I am marking that on the board. We will answer it in one step and return to the lesson."
    )
    speech = _plain(speech, MAX_SPEECH)
    board = _answer_board(
        topic,
        question,
        speech,
        [
            {"op": "title", "text": "Question"},
            {"op": "hand", "text": short},
            {
                "op": "figure",
                "kind": "list",
                "labels": ["Start from what you know", "Name the unclear part"],
            },
        ],
    )
    return {"speech": speech, "board": board, "source": "scaffold"}


def extract_json_object(text: str) -> dict[str, Any] | None:
    raw = _THINK.sub("", text or "")
    fence = _FENCE.search(raw)
    if fence:
        raw = fence.group(1)
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        data = json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    return data


def router_complete(router: Any, prompt: str) -> str:
    """Ask the local model. Never selects a usage-billed backend."""
    from .agent_builder import interviewer_model
    from .model_router import CompletionRequest

    providers = router.list_providers()
    ollama = next((row for row in providers if row.get("id") == "ollama"), None)
    installed = [str(name) for name in ((ollama or {}).get("models") or []) if name]
    enabled = bool((ollama or {}).get("enabled"))
    if enabled and installed:
        backend = "ollama"
        model = interviewer_model(installed)
    else:
        backend = "fake"
        model = "fake-instruct"
    done = router.complete(
        CompletionRequest(
            model=model,
            prompt=prompt,
            backend=backend,
            system=INSTRUCTOR_SYSTEM,
        )
    )
    return str(done.text or "")


def _call_model(complete: Callable[[str], str] | None, prompt: str) -> str:
    if complete is None:
        return ""
    try:
        return str(complete(prompt) or "")
    except Exception:
        return ""


def _sanitize_lesson(topic: str, data: dict[str, Any]) -> dict[str, Any]:
    title = _plain(data.get("title"), MAX_TEXT) or topic
    objectives = _objectives(data.get("objectives"))
    segments: list[dict[str, Any]] = []
    raw_segments = data.get("segments")
    if isinstance(raw_segments, list):
        for row in raw_segments[:MAX_SEGMENTS]:
            if not isinstance(row, dict):
                continue
            speech = _plain(row.get("speech"), MAX_SPEECH)
            if not speech:
                continue
            seg_title = _plain(row.get("title"), 80) or f"Part {len(segments) + 1}"
            segments.append(
                {
                    "id": f"s{len(segments) + 1}",
                    "title": seg_title,
                    "speech": speech,
                    "board": _board_or_title(row.get("board"), seg_title),
                }
            )
    if not objectives:
        objectives = [seg["title"] for seg in segments[:MAX_OBJECTIVES]] or [title]
    return {
        "topic": topic,
        "title": title,
        "objectives": objectives,
        "source": "model",
        "segments": _illustrate_network(topic, segments),
    }


def _board_or_title(raw: Any, title: str) -> list[dict[str, Any]]:
    board = _sanitize_board(raw)
    if board:
        return board
    return [{"op": "title", "text": title}]


def _sanitize_board(raw: Any) -> list[dict[str, Any]]:
    return _compose_page(raw)


def _objectives(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for item in raw:
        text = _plain(item, 140)
        if text and text not in out:
            out.append(text)
        if len(out) >= MAX_OBJECTIVES:
            break
    return out


def _segment(title: str, speech: str, board: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "id": "",
        "title": title,
        "speech": _plain(speech, MAX_SPEECH),
        "board": _sanitize_board(board),
    }


def _plain(value: Any, limit: int) -> str:
    text = _TAG.sub("", str(value or ""))
    text = "".join(ch for ch in text if ch.isprintable())
    text = " ".join(text.split())
    return text[:limit].strip()


def _spoken_topic(topic: str) -> str:
    if len(topic) <= 80:
        return topic
    return topic[:77].rstrip() + "..."


def _ink(row: dict[str, Any]) -> str:
    value = str(row.get("ink") or "").strip().lower()
    if value in INK_COLORS:
        return value
    return ""


def _mark(value: Any, limit: int) -> str:
    text = _plain(value, limit)
    if len(text) < 2:
        return ""
    return text


def _label_list(raw: Any, limit: int) -> list[str]:
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for item in raw:
        if isinstance(item, dict):
            text = _mark(item.get("text") or item.get("label"), limit)
        else:
            text = _mark(item, limit)
        if text and text not in out:
            out.append(text)
        if len(out) >= limit:
            break
    return out


def _remember(items: list[str], text: str, limit: int) -> None:
    if text and text not in items and len(items) < limit:
        items.append(text)


def _match_key(key: str, labels: list[str]) -> str:
    if not key:
        return ""
    for label in labels:
        if label.lower() == key.lower():
            return label
    for label in labels:
        if key.lower() in label.lower():
            return label
    return ""


def _fit_labels(kind: str, labels: list[str]) -> list[str]:
    caps = {
        "flow": 3,
        "packet": 6,
        "layers": 6,
        "pie": 4,
        "cycle": 4,
        "equation": 1,
        "graph": 1,
        "list": 5,
        "fabric": 9,
    }
    return labels[: caps.get(kind, 4)]


def _read_table(row: dict[str, Any]) -> tuple[list[str], list[list[str]]]:
    columns = _label_list(row.get("columns"), 2)
    raw_rows = row.get("rows")
    if len(columns) < 2 or not isinstance(raw_rows, list):
        return [], []
    rows: list[list[str]] = []
    for item in raw_rows[:MAX_ROWS]:
        if isinstance(item, dict):
            cells = [_plain(item.get("a"), 48), _plain(item.get("b"), 48)]
        elif isinstance(item, list):
            cells = [_plain(cell, 48) for cell in item[:2]]
        else:
            continue
        while len(cells) < 2:
            cells.append("")
        if any(cells):
            rows.append(cells[:2])
    if not rows:
        return [], []
    return columns[:2], rows


def _name_list(raw: Any, limit: int) -> list[str]:
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, list):
        return []
    names: list[str] = []
    for item in raw:
        if isinstance(item, dict):
            text = _mark(item.get("text") or item.get("label"), 24)
        else:
            text = _mark(item, 24)
        if text:
            names.append(text)
        if len(names) >= limit:
            break
    return names


def _fabric_groups(labels: list[str]) -> tuple[list[str], list[str], list[str]]:
    spines: list[str] = []
    leaves: list[str] = []
    hosts: list[str] = []
    for label in labels:
        low = label.lower()
        if "spine" in low and len(spines) < 2:
            spines.append(label)
        elif any(word in low for word in ("leaf", "vtep")) and len(leaves) < 3:
            leaves.append(label)
        elif any(word in low for word in ("host", "server")) and len(hosts) < 4:
            hosts.append(label)
    if spines or leaves or hosts:
        return spines, leaves, hosts
    spines = labels[:2]
    leaves = labels[2:4]
    hosts = labels[4:6]
    return spines, leaves, hosts


def _compose_page(raw: Any) -> list[dict[str, Any]]:
    """Turn model marks into one page: title, one figure, notes, optional table."""
    if not isinstance(raw, list):
        return []
    title = ""
    labels: list[str] = []
    hands: list[str] = []
    kind = ""
    key = ""
    explicit = False
    locked_labels = False
    packet = False
    spines: list[str] = []
    leaves: list[str] = []
    hosts: list[str] = []
    tunnel = ""
    columns: list[str] = []
    rows: list[list[str]] = []
    for row in raw[:MAX_OPS]:
        if not isinstance(row, dict):
            continue
        op = str(row.get("op") or "").strip().lower()
        if op in {"", "clear"}:
            continue
        if op == "title" and not title:
            title = _mark(row.get("text"), 80)
            continue
        if op == "table" and not rows:
            columns, rows = _read_table(row)
            continue
        if op == "figure":
            requested = str(row.get("kind") or "").strip().lower()
            if requested in FIGURES:
                kind = requested
                explicit = True
            found = _label_list(row.get("labels"), MAX_LABELS)
            text = _mark(row.get("text"), 48)
            if text and text not in found:
                found.insert(0, text)
            if requested == "fabric":
                spines = _name_list(row.get("spines"), 2)
                leaves = _name_list(row.get("leaves"), 3)
                hosts = _name_list(row.get("hosts"), 4)
                tunnel = _mark(row.get("tunnel"), 24)
                if not found:
                    found = spines + leaves + hosts
            if found:
                labels = found[:9]
                locked_labels = True
            marked = _mark(row.get("key"), 48)
            if marked:
                key = marked
            if _ink(row) == "red" and text:
                key = text
            continue
        if op in {"hand", "bullet", "write"}:
            _remember(hands, _mark(row.get("text"), 110), 6)
            continue
        if op in {"label", "box", "sketch", "circle", "arrow"}:
            text = _mark(row.get("text"), 48)
            if not locked_labels:
                _remember(labels, text, MAX_LABELS)
            sketch = str(row.get("kind") or "").strip().lower()
            if op == "sketch" and sketch == "packet":
                packet = True
            if _ink(row) == "red" and text:
                key = text
            continue
    promoted = False
    if not labels and hands:
        labels = [_mark(line, 48) for line in hands[:5]]
        labels = [line for line in labels if line]
        hands = []
        if not explicit:
            kind = "list"
            promoted = True
    if not explicit and not promoted:
        if any(_PERCENT.search(label) for label in labels):
            kind = "pie"
        elif len(labels) == 1 and _EQUALS.match(labels[0]):
            kind = "equation"
        elif packet:
            kind = "packet"
        elif len(labels) >= 2:
            kind = "flow"
        elif len(labels) == 1:
            kind = "layers"
        else:
            kind = ""
    if kind not in FIGURES:
        kind = ""
    labels = _fit_labels(kind, labels) if kind else []
    key = _match_key(key, labels)
    page: list[dict[str, Any]] = []
    if title:
        page.append({"op": "title", "text": title})
    if kind == "fabric":
        if not (spines or leaves or hosts):
            spines, leaves, hosts = _fabric_groups(labels)
        labels = (spines + leaves + hosts) or labels
        key = _match_key(key, labels)
        if not tunnel:
            tunnel = "VXLAN" if any("vxlan" in label.lower() for label in labels) else "overlay"
        if len(spines) + len(leaves) + len(hosts) < 2:
            kind = ""
    if kind and (labels or kind == "fabric"):
        figure: dict[str, Any] = {"op": "figure", "kind": kind, "labels": labels}
        if key:
            figure["key"] = key
        if kind == "fabric":
            figure["spines"] = spines
            figure["leaves"] = leaves
            figure["hosts"] = hosts
            figure["tunnel"] = tunnel or "overlay"
        page.append(figure)
    for line in hands[:MAX_HAND]:
        if line not in labels:
            page.append({"op": "hand", "text": line})
    if columns and rows:
        page.append({"op": "table", "columns": columns, "rows": rows})
    return page


def _vxlan_packet(title: str) -> list[dict[str, Any]]:
    return _compose_page(
        [
            {"op": "title", "text": title or "VXLAN header"},
            {
                "op": "figure",
                "kind": "packet",
                "labels": ["Outer IP", "UDP 4789", "VXLAN", "VNI", "Inner frame"],
                "key": "VNI",
            },
            {"op": "hand", "text": "The underlay routes only the outer IP. The VNI names the virtual network."},
        ]
    )


def _vxlan_fabric(title: str) -> list[dict[str, Any]]:
    return _compose_page(
        [
            {"op": "title", "text": title or "VXLAN fabric"},
            {
                "op": "figure",
                "kind": "fabric",
                "spines": ["Spine", "Spine"],
                "leaves": ["Leaf A", "Leaf B"],
                "hosts": ["Host A", "Host B"],
                "tunnel": "VXLAN",
                "key": "Leaf A",
            },
            {"op": "hand", "text": "Each leaf is a VTEP. It wraps the Ethernet frame in UDP."},
            {"op": "hand", "text": "Spines forward the outer IP. The VNI stays hidden in the overlay."},
        ]
    )


def _note_board(which: str) -> list[dict[str, Any]]:
    """Marks added onto a diagram that is already on the board."""
    if which == "example":
        return [
            {"op": "emphasis", "target": "tunnel", "text": "VXLAN", "ink": "green"},
            {
                "op": "hand",
                "text": "Follow Host A into Leaf A, across the tunnel, and out at Leaf B.",
                "ink": "green",
            },
        ]
    if which == "check":
        return [
            {
                "op": "hand",
                "text": "Point at the leaf that wraps the frame, and name what the spine sees.",
                "ink": "green",
            },
        ]
    return [
        {"op": "emphasis", "target": "leaves", "text": "VTEP", "ink": "green"},
        {"op": "hand", "text": "Green marks the VTEPs on the same fabric. Blue stays the underlay.", "ink": "green"},
    ]


def _illustrate_network(topic: str, segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Draw the fabric once. Later sections add marks on that same diagram."""
    if not _NETWORK.search(topic):
        return segments
    shown = False
    for segment in segments:
        title = str(segment.get("title") or "")
        low = title.lower()
        blob = f"{title} {segment.get('speech') or ''}".lower()
        if any(word in low for word in ("open", "plan")) and "example" not in low:
            segment["place"] = "page"
            continue
        pictorial = any(word in low for word in ("defin", "purpose", "component", "part", "example", "fabric", "header")) or any(
            word in blob for word in ("encapsul", "spine", "leaf", "vtep", "header", "topology")
        )
        quiz = any(word in low for word in ("check", "review", "question"))
        existing = next((op for op in segment.get("board") or [] if op.get("op") == "figure"), None)
        if not shown and pictorial and existing and existing.get("kind") == "packet":
            segment["place"] = "page"
            continue
        if not shown and pictorial:
            segment["board"] = _vxlan_fabric(title or "VXLAN fabric")
            segment["place"] = "page"
            shown = True
            continue
        if shown and (pictorial or quiz):
            which = "example" if "example" in low else "check" if quiz else "parts"
            segment["board"] = _note_board(which)
            segment["place"] = "add"
    return segments


def _answer_board(topic: str, question: str, speech: str, board: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """A spoken answer still draws. A clean-slate or fabric request draws the network again."""
    figure = next((op for op in board if op.get("op") == "figure"), None)
    blob = f"{topic} {question} {speech}"
    fresh = bool(_FRESH.search(question))
    asks_fabric = bool(_FABRIC_ASK.search(question)) or (
        bool(_FABRIC_ASK.search(speech)) and bool(re.search(r"\b(draw|sketch|diagram|show|redraw|clean)\b", question, re.IGNORECASE))
    )
    if (fresh or asks_fabric) and _NETWORK.search(blob) and (fresh or figure is None or figure.get("kind") != "fabric"):
        return _vxlan_fabric("VXLAN fabric")
    if asks_fabric and (figure is None or figure.get("kind") != "fabric"):
        return _vxlan_fabric("The fabric")
    if figure is None:
        return _spoken_page(question, speech)
    return board


def _spoken_page(question: str, speech: str) -> list[dict[str, Any]]:
    title = _mark(question, 42) or "Answer"
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", speech) if len(part.strip()) > 8]
    labels = [line for line in (_mark(part, 48) for part in sentences[:4]) if line]
    if not labels:
        labels = ["Start from what you know", "Name the unclear part"]
    return _compose_page(
        [
            {"op": "title", "text": title},
            {"op": "figure", "kind": "list", "labels": labels},
        ]
    )


_POST_ID = re.compile(r"^[0-9a-f]{32}$")


def posts_root() -> Path:
    override = os.environ.get("AI_LAB_CLASSROOM_POSTS", "").strip()
    root = Path(override) if override else Path.home() / ".ai-lab" / "classroom" / "posts"
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    return root


def save_post(
    *,
    topic: str,
    title: str,
    lesson: dict[str, Any] | None = None,
    discussion: list[Any] | None = None,
    image_png: str = "",
    root: Path | None = None,
) -> dict[str, Any]:
    clean_topic = _plain(topic, MAX_TOPIC)
    clean_title = _plain(title, MAX_TEXT) or clean_topic
    if not clean_title:
        raise ValueError("title is required")
    stored_lesson: dict[str, Any] | None = None
    if isinstance(lesson, dict) and lesson:
        stored_lesson = _sanitize_lesson(clean_topic or clean_title, lesson)
        if clean_topic:
            stored_lesson["topic"] = clean_topic
    turns = _discussion(discussion)
    folder = root or posts_root()
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    post_id = uuid.uuid4().hex
    body = {
        "id": post_id,
        "topic": clean_topic,
        "title": clean_title,
        "created": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "lesson": stored_lesson,
        "discussion": turns,
        "image": False,
    }
    if image_png:
        blob = decode_png(image_png)
        _post_file(folder, post_id, ".png").write_bytes(blob)
        body["image"] = True
    _post_file(folder, post_id, ".json").write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    return body


def list_posts(root: Path | None = None) -> list[dict[str, Any]]:
    folder = root or posts_root()
    if not folder.is_dir():
        return []
    rows: list[dict[str, Any]] = []
    for path in folder.glob("*.json"):
        if not _POST_ID.match(path.stem):
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        rows.append(
            {
                "id": path.stem,
                "title": _plain(data.get("title"), MAX_TEXT),
                "topic": _plain(data.get("topic"), MAX_TOPIC),
                "created": _plain(data.get("created"), 40),
                "image": bool(data.get("image")),
            }
        )
    rows.sort(key=lambda row: row.get("created") or "", reverse=True)
    return rows[:40]


def load_post(post_id: str, root: Path | None = None) -> dict[str, Any]:
    folder = root or posts_root()
    path = _post_file(folder, post_id, ".json")
    if not path.is_file():
        raise ValueError("post not found")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("post not found")
    data["id"] = post_id
    return data


def load_post_image(post_id: str, root: Path | None = None) -> bytes:
    path = _post_file(root or posts_root(), post_id, ".png")
    if not path.is_file():
        raise ValueError("post not found")
    blob = path.read_bytes()
    if not blob.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("post not found")
    return blob


def decode_png(data: str) -> bytes:
    raw = str(data or "").strip()
    if raw.startswith("data:"):
        raw = raw.split(",", 1)[-1]
    try:
        blob = base64.b64decode(raw, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError("image must be a PNG") from exc
    if len(blob) > MAX_POST_PNG or not blob.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("image must be a PNG")
    return blob


def _discussion(raw: list[Any] | None) -> list[dict[str, str]]:
    if not isinstance(raw, list):
        return []
    turns: list[dict[str, str]] = []
    for row in raw[:30]:
        if not isinstance(row, dict):
            continue
        who = "Instructor" if str(row.get("who") or "") == "Instructor" else "You"
        text = _plain(row.get("text"), MAX_QUESTION)
        if text:
            turns.append({"who": who, "text": text})
    return turns


def _post_file(root: Path, post_id: str, suffix: str) -> Path:
    if not _POST_ID.match(post_id):
        raise ValueError("post not found")
    folder = root.resolve()
    path = (folder / f"{post_id}{suffix}").resolve()
    try:
        path.relative_to(folder)
    except ValueError as exc:
        raise ValueError("post not found") from exc
    return path

