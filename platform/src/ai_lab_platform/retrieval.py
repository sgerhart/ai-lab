"""Scoped retrieval memory (FEAT-008 / IWO-040).

Hash embeddings by default (no model pull). Optional Qdrant HTTP when
``QDRANT_URL`` + ``QDRANT_API_KEY`` are set. Never invent citations: empty
search returns an explicit no-match note.
"""

from __future__ import annotations

import hashlib
import math
import os
import re
from dataclasses import dataclass, field
from typing import Any, Protocol
from uuid import uuid4
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .work_order import utcnow

VECTOR_SIZE = 64
NO_MATCH_NOTE = (
    "no matches — do not invent citations or sources (FEAT-008 citation policy)"
)
_TOKEN_RE = re.compile(r"[a-z0-9]+", re.I)


def hash_embed(text: str, *, dims: int = VECTOR_SIZE) -> list[float]:
    """Deterministic bag-of-tokens embedding (L2-normalized). No model weights."""
    vec = [0.0] * dims
    tokens = _TOKEN_RE.findall((text or "").lower())
    if not tokens:
        return vec
    for tok in tokens:
        digest = hashlib.sha256(tok.encode("utf-8")).digest()
        idx = int.from_bytes(digest[:4], "big") % dims
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vec[idx] += sign
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


@dataclass
class MemoryDocument:
    id: str
    text: str
    source: str
    meta: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "source": self.source,
            "meta": self.meta,
            "created_at": self.created_at,
        }


@dataclass
class MemoryHit:
    id: str
    text: str
    source: str
    score: float
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "source": self.source,
            "score": self.score,
            "meta": self.meta,
        }


class MemoryStore(Protocol):
    def upsert(self, doc: MemoryDocument, vector: list[float]) -> None: ...

    def search(
        self, vector: list[float], *, limit: int = 5, project_id: str | None = None
    ) -> list[MemoryHit]: ...

    def list_documents(self, *, project_id: str) -> list[MemoryHit]: ...

    def delete(self, doc_id: str) -> bool: ...

    def status(self) -> dict[str, Any]: ...


class InMemoryStore:
    """Unit-test / fallback store (cosine over hash embeds)."""

    def __init__(self) -> None:
        self._rows: list[tuple[MemoryDocument, list[float]]] = []

    def upsert(self, doc: MemoryDocument, vector: list[float]) -> None:
        self._rows = [(d, v) for d, v in self._rows if d.id != doc.id]
        self._rows.append((doc, list(vector)))

    def search(
        self, vector: list[float], *, limit: int = 5, project_id: str | None = None
    ) -> list[MemoryHit]:
        scored: list[MemoryHit] = []
        for doc, vec in self._rows:
            if project_id and str(doc.meta.get("project_id") or "") != project_id:
                continue
            score = _cosine(vector, vec)
            scored.append(
                MemoryHit(
                    id=doc.id,
                    text=doc.text,
                    source=doc.source,
                    score=score,
                    meta=dict(doc.meta),
                )
            )
        scored.sort(key=lambda h: h.score, reverse=True)
        return scored[: max(1, limit)]

    def list_documents(self, *, project_id: str) -> list[MemoryHit]:
        found = [
            MemoryHit(
                id=doc.id,
                text=doc.text,
                source=doc.source,
                score=0.0,
                meta=dict(doc.meta),
            )
            for doc, _vec in self._rows
            if str(doc.meta.get("project_id") or "") == project_id
        ]
        found.sort(key=lambda hit: hit.source)
        return found

    def delete(self, doc_id: str) -> bool:
        before = len(self._rows)
        self._rows = [(doc, vec) for doc, vec in self._rows if doc.id != doc_id]
        return len(self._rows) < before

    def status(self) -> dict[str, Any]:
        return {
            "backend": "memory",
            "documents": len(self._rows),
            "vector_size": VECTOR_SIZE,
            "ok": True,
        }


class QdrantStore:
    """Minimal Qdrant REST client (API key required — ADR 0024)."""

    def __init__(
        self,
        *,
        url: str,
        api_key: str,
        collection: str = "ai_lab_memory",
        timeout: float = 8.0,
    ) -> None:
        self.url = url.rstrip("/")
        self.api_key = api_key
        self.collection = collection
        self.timeout = timeout
        self._ensured = False

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "api-key": self.api_key,
        }

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        import json

        data = None if body is None else json.dumps(body).encode("utf-8")
        req = Request(
            f"{self.url}{path}",
            data=data,
            headers=self._headers(),
            method=method,
        )
        try:
            with urlopen(req, timeout=self.timeout) as resp:  # noqa: S310 — operator URL
                raw = resp.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"qdrant_http_{exc.code}:{detail[:400]}") from exc
        except URLError as exc:
            raise RuntimeError(f"qdrant_unreachable:{exc}") from exc
        if not raw:
            return {}
        return json.loads(raw)

    def ensure_collection(self) -> None:
        if self._ensured:
            return
        try:
            self._request("GET", f"/collections/{self.collection}")
            self._ensured = True
            return
        except RuntimeError:
            pass
        self._request(
            "PUT",
            f"/collections/{self.collection}",
            {
                "vectors": {
                    "size": VECTOR_SIZE,
                    "distance": "Cosine",
                }
            },
        )
        self._ensured = True

    def upsert(self, doc: MemoryDocument, vector: list[float]) -> None:
        self.ensure_collection()
        self._request(
            "PUT",
            f"/collections/{self.collection}/points?wait=true",
            {
                "points": [
                    {
                        "id": doc.id,
                        "vector": vector,
                        "payload": {
                            "text": doc.text,
                            "source": doc.source,
                            "meta": doc.meta,
                            "created_at": doc.created_at,
                        },
                    }
                ]
            },
        )

    def search(
        self, vector: list[float], *, limit: int = 5, project_id: str | None = None
    ) -> list[MemoryHit]:
        self.ensure_collection()
        body: dict[str, Any] = {
            "vector": vector,
            "limit": max(1, limit),
            "with_payload": True,
        }
        if project_id:
            body["filter"] = qdrant_project_filter(project_id)
        data = self._request(
            "POST",
            f"/collections/{self.collection}/points/search",
            body,
        )
        hits: list[MemoryHit] = []
        for row in data.get("result") or []:
            payload = row.get("payload") or {}
            hits.append(
                MemoryHit(
                    id=str(row.get("id")),
                    text=str(payload.get("text") or ""),
                    source=str(payload.get("source") or ""),
                    score=float(row.get("score") or 0.0),
                    meta=dict(payload.get("meta") or {}),
                )
            )
        if project_id:
            hits = [hit for hit in hits if str(hit.meta.get("project_id") or "") == project_id]
        return hits

    def list_documents(self, *, project_id: str) -> list[MemoryHit]:
        self.ensure_collection()
        data = self._request(
            "POST",
            f"/collections/{self.collection}/points/scroll",
            {
                "filter": qdrant_project_filter(project_id),
                "limit": 100,
                "with_payload": True,
                "with_vector": False,
            },
        )
        result = data.get("result") or {}
        points = result.get("points") if isinstance(result, dict) else []
        hits: list[MemoryHit] = []
        for row in points or []:
            payload = row.get("payload") or {}
            meta = dict(payload.get("meta") or {})
            if str(meta.get("project_id") or "") != project_id:
                continue
            hits.append(
                MemoryHit(
                    id=str(row.get("id")),
                    text=str(payload.get("text") or ""),
                    source=str(payload.get("source") or ""),
                    score=0.0,
                    meta=meta,
                )
            )
        hits.sort(key=lambda hit: hit.source)
        return hits

    def delete(self, doc_id: str) -> bool:
        self.ensure_collection()
        self._request(
            "POST",
            f"/collections/{self.collection}/points/delete?wait=true",
            {"points": [doc_id]},
        )
        return True

    def status(self) -> dict[str, Any]:
        try:
            self.ensure_collection()
            info = self._request("GET", f"/collections/{self.collection}")
            result = info.get("result") or {}
            points = (result.get("points_count") if isinstance(result, dict) else None)
            return {
                "backend": "qdrant",
                "url": self.url,
                "collection": self.collection,
                "documents": points,
                "vector_size": VECTOR_SIZE,
                "ok": True,
            }
        except RuntimeError as exc:
            return {
                "backend": "qdrant",
                "url": self.url,
                "collection": self.collection,
                "ok": False,
                "error": str(exc),
                "vector_size": VECTOR_SIZE,
            }


def qdrant_project_filter(project_id: str) -> dict[str, Any]:
    return {"must": [{"key": "meta.project_id", "match": {"value": project_id}}]}


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    return sum(x * y for x, y in zip(a, b, strict=True))


def build_memory_store_from_env() -> MemoryStore:
    url = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333").strip()
    key = os.environ.get("QDRANT_API_KEY", "").strip()
    collection = os.environ.get("AI_LAB_MEMORY_COLLECTION", "ai_lab_memory").strip()
    force_memory = os.environ.get("AI_LAB_MEMORY_BACKEND", "").strip().lower() == "memory"
    if force_memory or not key:
        return InMemoryStore()
    store = QdrantStore(url=url, api_key=key, collection=collection or "ai_lab_memory")
    # Prefer Qdrant when key is set; callers can fall back on status.ok == False.
    return store


class RetrievalService:
    """Upsert/search with citation-safe response shaping."""

    def __init__(self, store: MemoryStore | None = None) -> None:
        self.store = store or InMemoryStore()

    def upsert(
        self,
        *,
        text: str,
        source: str,
        doc_id: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        body = (text or "").strip()
        src = (source or "").strip()
        if not body:
            raise ValueError("text required")
        if not src:
            raise ValueError("source required (citation policy)")
        doc = MemoryDocument(
            id=doc_id or str(uuid4()),
            text=body,
            source=src,
            meta=dict(meta or {}),
        )
        self.store.upsert(doc, hash_embed(body))
        return doc.to_dict()

    def search(
        self, query: str, *, limit: int = 5, project_id: str | None = None
    ) -> dict[str, Any]:
        q = (query or "").strip()
        if not q:
            raise ValueError("query required")
        scoped = (project_id or "").strip() or None
        hits = self.store.search(hash_embed(q), limit=limit, project_id=scoped)
        return {
            "ok": True,
            "query": q,
            "project_id": scoped or "",
            "matches": [h.to_dict() for h in hits],
            "note": NO_MATCH_NOTE if not hits else "cite only sources listed in matches",
        }

    def add_project_document(
        self,
        *,
        project_id: str,
        text: str,
        source: str,
        filename: str = "",
    ) -> dict[str, Any]:
        saved = self.upsert(
            text=text,
            source=source,
            meta={"project_id": project_id, "filename": filename or source},
        )
        return saved

    def list_project_documents(self, project_id: str) -> list[dict[str, Any]]:
        hits = self.store.list_documents(project_id=project_id)
        return [
            {
                "id": hit.id,
                "source": hit.source,
                "filename": str(hit.meta.get("filename") or hit.source),
                "bytes": len(hit.text.encode("utf-8")),
            }
            for hit in hits
        ]

    def delete_document(self, doc_id: str, *, project_id: str) -> bool:
        owned = any(hit.id == doc_id for hit in self.store.list_documents(project_id=project_id))
        if not owned:
            return False
        return self.store.delete(doc_id)

    def project_context(self, query: str, project_id: str, *, limit: int = 3) -> str:
        scoped = (project_id or "").strip()
        if not scoped or not (query or "").strip():
            return ""
        result = self.search(query, limit=limit, project_id=scoped)
        parts: list[str] = []
        for hit in result["matches"]:
            source = hit.get("source") or hit.get("id")
            text = str(hit.get("text") or "")[:4000]
            if text:
                parts.append(f"[{source}]\n{text}")
        if not parts:
            return ""
        return "Project documents (cite only these sources):\n" + "\n\n".join(parts)

    def status(self) -> dict[str, Any]:
        st = self.store.status()
        st["embedding"] = "hash_v1"
        st["citation_policy"] = "no-fabrication"
        return st


def memory_search_tool(query: str, *, limit: int = 5, service: RetrievalService | None = None) -> str:
    """Agent-facing observation string for ``memory_search``."""
    import json

    svc = service or default_retrieval_service()
    try:
        result = svc.search(query, limit=limit)
    except ValueError as exc:
        return f"memory_search error: {exc}"
    return json.dumps(result, indent=2)


def memory_write_tool(
    text: str,
    source: str,
    *,
    doc_id: str | None = None,
    service: RetrievalService | None = None,
) -> str:
    """Agent-facing observation for privileged ``memory_write`` (IWO-041)."""
    import json

    svc = service or default_retrieval_service()
    doc = svc.upsert(text=text, source=source, doc_id=doc_id)
    return json.dumps({"ok": True, "written": doc}, indent=2)


_default_service: RetrievalService | None = None


def default_retrieval_service() -> RetrievalService:
    global _default_service
    if _default_service is None:
        _default_service = RetrievalService(build_memory_store_from_env())
    return _default_service


def set_default_retrieval_service(service: RetrievalService | None) -> None:
    global _default_service
    _default_service = service


__all__ = [
    "InMemoryStore",
    "MemoryDocument",
    "MemoryHit",
    "NO_MATCH_NOTE",
    "QdrantStore",
    "RetrievalService",
    "VECTOR_SIZE",
    "build_memory_store_from_env",
    "default_retrieval_service",
    "hash_embed",
    "memory_search_tool",
    "memory_write_tool",
    "set_default_retrieval_service",
]
