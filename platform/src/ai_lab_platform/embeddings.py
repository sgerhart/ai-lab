"""Text embeddings for saved pages.

Hash embeddings stay the default so tests and a machine without the local
model keep working. When fastembed is installed, a small English model ranks
a later question against a saved page even if the words differ.
"""

from __future__ import annotations

import math
import os
from typing import Protocol

from .retrieval import hash_embed

_DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"


class Embedder(Protocol):
    name: str

    def embed(self, text: str, *, query: bool = False) -> list[float]: ...


class HashEmbedder:
    name = "hash_v1"

    def embed(self, text: str, *, query: bool = False) -> list[float]:
        return hash_embed(text)


class OnnxEmbedder:
    """Local ONNX embedder. The weights download on first use and stay off Git."""

    def __init__(self, model_name: str = _DEFAULT_MODEL) -> None:
        self.model_name = model_name
        self.name = "bge-small-en-v1.5"
        self._model: object | None = None

    def embed(self, text: str, *, query: bool = False) -> list[float]:
        if self._model is None:
            from fastembed import TextEmbedding

            self._model = TextEmbedding(self.model_name)
        body = (text or "").strip()[:4000] or " "
        if query:
            body = "Represent this sentence for searching relevant passages: " + body
        vector = next(iter(self._model.embed([body])))  # type: ignore[attr-defined]
        return [float(value) for value in vector]


def cosine(left: list[float], right: list[float]) -> float:
    if not left or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return dot / (left_norm * right_norm)


def build_embedder() -> Embedder:
    """Real embeddings when the package is installed. Otherwise the hash."""
    flag = os.environ.get("AI_LAB_EMBED", "on").strip().lower()
    if flag in {"0", "off", "false", "no"}:
        return HashEmbedder()
    try:
        import fastembed  # noqa: F401
    except ImportError:
        return HashEmbedder()
    model_name = os.environ.get("AI_LAB_EMBED_MODEL", _DEFAULT_MODEL).strip() or _DEFAULT_MODEL
    return OnnxEmbedder(model_name)
