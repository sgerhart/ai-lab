"""Machine-readable model catalog. Weights are not in Git and are not pulled from here."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class PullRefused(RuntimeError):
    """Raised when any code path tries to download weights."""


def catalog_path() -> Path:
    return Path(__file__).resolve().parents[3] / "models" / "catalog.json"


def load_catalog(path: Path | None = None) -> dict[str, Any]:
    target = path or catalog_path()
    data = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("catalog root must be an object")
    models = data.get("models")
    if not isinstance(models, list):
        raise ValueError("catalog.models must be a list")
    for item in models:
        if not isinstance(item, dict) or not item.get("id"):
            raise ValueError("each catalog model needs an id")
        if item.get("pull_authorized") is True:
            raise ValueError(f"{item['id']}: pull_authorized must stay false until a human ADR/work order says otherwise")
        status = str(item.get("status") or "")
        if status in {"pulled", "ready", "live"}:
            raise ValueError(f"{item['id']}: catalog must not claim status={status!r} from Git alone")
    return data


def listed_ids(path: Path | None = None) -> list[str]:
    data = load_catalog(path)
    return [str(item["id"]) for item in data.get("models") or []]


def refuse_pull(model_id: str = "") -> None:
    suffix = f" ({model_id})" if model_id else ""
    raise PullRefused(
        f"Refusing to pull weights{suffix}. Use docs/runbooks/adding-a-model.md after human authorization."
    )


@dataclass(frozen=True)
class CatalogSummary:
    schema_version: int
    host: str
    model_count: int
    pulled_in_git: bool = False
