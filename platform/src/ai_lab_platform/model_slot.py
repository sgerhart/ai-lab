"""Decide whether an Ollama request may load a model.

A request continues when Ollama has that model in memory, or when nothing is
loaded. A different resident model, such as the Jupyter coding model, keeps
the request waiting. This module does not pull weights or set context size.
"""

from __future__ import annotations

import json
from typing import Any
from urllib.request import Request, urlopen


class ModelSlotBusy(RuntimeError):
    """Another model is in memory. The caller must not load a second one."""


def model_tag(name: str) -> str:
    return (name or "").strip().split()[0].split("@")[0].lower()


def same_model(wanted: str, loaded: str) -> bool:
    wanted_tag = model_tag(wanted)
    loaded_tag = model_tag(loaded)
    return bool(wanted_tag) and wanted_tag == loaded_tag


def slot_note(needed: str, loaded: list[str]) -> str | None:
    """None means the request may continue. A sentence means it waits."""
    display: list[str] = []
    for name in loaded:
        tag = (name or "").strip().split()[0].split("@")[0]
        if tag and tag.lower() not in {item.lower() for item in display}:
            display.append(tag)
    if not display:
        return None
    if any(same_model(needed, name) for name in display):
        return None
    busy = ", ".join(display)
    verb = "are" if len(display) > 1 else "is"
    want = model_tag(needed) or "the requested model"
    return f"{busy} {verb} loaded. This waits until Ollama is free, then uses {want}."


def read_resident(base_url: str, *, timeout: float = 2.0) -> list[str] | None:
    """Names from Ollama /api/ps. None when the probe does not answer."""
    url = (base_url or "").rstrip("/") + "/api/ps"
    try:
        req = Request(url, method="GET")
        with urlopen(req, timeout=timeout) as resp:  # noqa: S310 — lab Ollama URL
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    names: list[str] = []
    for row in data.get("models") or []:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or row.get("model") or "").strip()
        if name:
            names.append(name)
    return names


def ensure_slot(base_url: str, model: str, reader: Any = None) -> None:
    loaded = reader() if reader is not None else read_resident(base_url)
    if loaded is None:
        return
    note = slot_note(model, list(loaded))
    if note:
        raise ModelSlotBusy(note)
