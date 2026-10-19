"""Knowledge Nexus Qdrant Book RAG Indexer & Semantic Search (IWO-105).

Provides chunking, neural embedding, indexing, and vector similarity search for
EPUB and PDF books stored in Knowledge Nexus (~/.ai-lab/nexus/04_Books_Library).
Uses the high-performance BAAI/bge-small-en-v1.5 neural transformer embedding
model (384-dim, ONNX runtime via fastembed) with graceful fallback to deterministic
hash embeddings when fastembed is unavailable.
"""

from __future__ import annotations

import json
import os
import re
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .attachments import pdf_text
from .nexus_study import find_nexus_root, format_book_title, resolve_book_file
from .retrieval import VECTOR_SIZE, hash_embed

COLLECTION_NAME = "nexus_books"
NEURAL_MODEL_NAME = "BAAI/bge-small-en-v1.5"
NEURAL_VECTOR_SIZE = 384

_embedder: Any | None = None
_embedder_initialized: bool = False


def get_embedder() -> Any | None:
    """Lazily load fastembed TextEmbedding model."""
    global _embedder, _embedder_initialized
    if not _embedder_initialized:
        _embedder_initialized = True
        try:
            from fastembed import TextEmbedding

            _embedder = TextEmbedding(model_name=NEURAL_MODEL_NAME)
        except Exception:
            _embedder = None
    return _embedder


def get_vector_size() -> int:
    """Return vector dimension based on available embedder."""
    if get_embedder() is not None:
        return NEURAL_VECTOR_SIZE
    return VECTOR_SIZE


def embed_text(text: str) -> list[float]:
    """Embed single text using BGE neural model or fallback hash_embed."""
    embedder = get_embedder()
    if embedder is not None:
        try:
            vecs = list(embedder.embed([text]))
            if vecs:
                return [float(x) for x in vecs[0]]
        except Exception:
            pass
    return hash_embed(text)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed batch of texts using fastembed neural model or fallback hash_embed."""
    embedder = get_embedder()
    if embedder is not None:
        try:
            vecs = list(embedder.embed(texts))
            return [[float(x) for x in v] for v in vecs]
        except Exception:
            pass
    return [hash_embed(t) for t in texts]


@dataclass
class NexusBookChunk:
    id: str
    title: str
    rel_path: str
    chapter: str
    text: str
    chunk_index: int
    score: float = 0.0

    def to_payload_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "rel_path": self.rel_path,
            "chapter": self.chapter,
            "text": self.text,
            "chunk_index": self.chunk_index,
        }


def chunk_epub(epub_path: Path, rel_path: str, title: str) -> list[NexusBookChunk]:
    """Chunk an EPUB by chapter and paragraph boundaries into ~600-1200 char segments."""
    chunks: list[NexusBookChunk] = []
    chunk_idx = 0

    try:
        with zipfile.ZipFile(epub_path, "r") as z:
            html_files = [
                f for f in z.namelist() if f.lower().endswith((".html", ".xhtml"))
            ]
            for fname in html_files:
                ch_label = Path(fname).stem.replace("-", " ").replace("_", " ").title()
                try:
                    raw = z.read(fname).decode("utf-8", errors="ignore")
                except Exception:
                    continue

                blocks = re.split(r"<(?:p|div|h[1-6]|section)[^>]*>", raw)
                cur_text: list[str] = []
                cur_len = 0

                for b in blocks:
                    cleaned = re.sub(r"<[^>]+>", " ", b).strip()
                    cleaned = re.sub(r"\s+", " ", cleaned)
                    if len(cleaned) < 30:
                        continue

                    cur_text.append(cleaned)
                    cur_len += len(cleaned)

                    if cur_len >= 600:
                        combined = " ".join(cur_text).strip()
                        c_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{rel_path}:{chunk_idx}"))
                        chunks.append(
                            NexusBookChunk(
                                id=c_id,
                                title=title,
                                rel_path=rel_path,
                                chapter=ch_label,
                                text=combined,
                                chunk_index=chunk_idx,
                            )
                        )
                        chunk_idx += 1
                        cur_text = []
                        cur_len = 0

                if cur_text:
                    combined = " ".join(cur_text).strip()
                    if len(combined) >= 40:
                        c_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{rel_path}:{chunk_idx}"))
                        chunks.append(
                            NexusBookChunk(
                                id=c_id,
                                title=title,
                                rel_path=rel_path,
                                chapter=ch_label,
                                text=combined,
                                chunk_index=chunk_idx,
                            )
                        )
                        chunk_idx += 1
    except Exception:
        pass

    return chunks


def chunk_pdf(pdf_path: Path, rel_path: str, title: str) -> list[NexusBookChunk]:
    """Chunk readable PDF text into segments of ~600-1200 characters."""
    chunks: list[NexusBookChunk] = []
    try:
        with open(pdf_path, "rb") as f:
            data = f.read(15_000_000)
        full_text = pdf_text(data)
        if not full_text:
            return chunks

        paragraphs = re.split(r"\n{2,}|\.\s+", full_text)
        cur_text: list[str] = []
        cur_len = 0
        chunk_idx = 0

        for p in paragraphs:
            cleaned = p.strip()
            if len(cleaned) < 25:
                continue

            cur_text.append(cleaned)
            cur_len += len(cleaned)

            if cur_len >= 600:
                combined = ". ".join(cur_text).strip()
                c_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{rel_path}:{chunk_idx}"))
                chunks.append(
                    NexusBookChunk(
                        id=c_id,
                        title=title,
                        rel_path=rel_path,
                        chapter="Document Content",
                        text=combined,
                        chunk_index=chunk_idx,
                    )
                )
                chunk_idx += 1
                cur_text = []
                cur_len = 0

        if cur_text:
            combined = ". ".join(cur_text).strip()
            if len(combined) >= 40:
                c_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{rel_path}:{chunk_idx}"))
                chunks.append(
                    NexusBookChunk(
                        id=c_id,
                        title=title,
                        rel_path=rel_path,
                        chapter="Document Content",
                        text=combined,
                        chunk_index=chunk_idx,
                    )
                )
    except Exception:
        pass

    return chunks


class NexusRagStore:
    """Qdrant client for Knowledge Nexus library books collection."""

    def __init__(
        self,
        *,
        url: str | None = None,
        api_key: str | None = None,
        collection: str = COLLECTION_NAME,
        timeout: float = 8.0,
    ) -> None:
        self.url = (url or os.environ.get("QDRANT_URL", "http://127.0.0.1:6333")).rstrip("/")
        self.api_key = api_key or os.environ.get("QDRANT_API_KEY", "")
        self.collection = collection
        self.timeout = timeout
        self._ensured = False

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["api-key"] = self.api_key
        return headers

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        data = None if body is None else json.dumps(body).encode("utf-8")
        req = Request(
            f"{self.url}{path}",
            data=data,
            headers=self._headers(),
            method=method,
        )
        try:
            with urlopen(req, timeout=self.timeout) as resp:  # noqa: S310
                raw = resp.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"qdrant_http_{exc.code}:{detail[:400]}") from exc
        except URLError as exc:
            raise RuntimeError(f"qdrant_unreachable:{exc}") from exc
        if not raw:
            return {}
        return json.loads(raw)

    def ensure_collection(self, recreate_if_mismatched: bool = True) -> bool:
        if self._ensured:
            return True
        target_size = get_vector_size()
        try:
            data = self._request("GET", f"/collections/{self.collection}")
            res = data.get("result") if isinstance(data, dict) else {}
            if isinstance(res, dict):
                params = res.get("config", {}).get("params", {})
                current_size = params.get("vectors", {}).get("size")
                if current_size == target_size:
                    self._ensured = True
                    return True
                if recreate_if_mismatched and current_size is not None and current_size != target_size:
                    self._request("DELETE", f"/collections/{self.collection}")
        except RuntimeError:
            pass

        try:
            self._request(
                "PUT",
                f"/collections/{self.collection}",
                {
                    "vectors": {
                        "size": target_size,
                        "distance": "Cosine",
                    }
                },
            )
            self._ensured = True
            return True
        except Exception:
            return False

    def upsert_chunks(self, chunks: list[NexusBookChunk], batch_size: int = 64) -> int:
        if not self.ensure_collection():
            return 0

        total_upserted = 0
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            texts = [c.text for c in batch]
            vecs = embed_texts(texts)

            points = [
                {
                    "id": c.id,
                    "vector": v,
                    "payload": c.to_payload_dict(),
                }
                for c, v in zip(batch, vecs, strict=False)
            ]
            try:
                self._request(
                    "PUT",
                    f"/collections/{self.collection}/points?wait=true",
                    {"points": points},
                )
                total_upserted += len(batch)
            except Exception:
                break

        return total_upserted

    def search(
        self, query: str, *, rel_path: str | None = None, limit: int = 4
    ) -> list[NexusBookChunk]:
        """Perform vector search in Qdrant for query."""
        if not self.ensure_collection():
            return []

        body: dict[str, Any] = {
            "vector": embed_text(query),
            "limit": max(1, limit),
            "with_payload": True,
        }
        if rel_path:
            clean_rel = rel_path.strip('"\'').lstrip("/\\")
            body["filter"] = {
                "must": [
                    {
                        "key": "rel_path",
                        "match": {"value": clean_rel},
                    }
                ]
            }

        try:
            data = self._request(
                "POST",
                f"/collections/{self.collection}/points/search",
                body,
            )
        except Exception:
            return []

        chunks: list[NexusBookChunk] = []
        for row in data.get("result") or []:
            payload = row.get("payload") or {}
            chunks.append(
                NexusBookChunk(
                    id=str(row.get("id")),
                    title=str(payload.get("title") or ""),
                    rel_path=str(payload.get("rel_path") or ""),
                    chapter=str(payload.get("chapter") or ""),
                    text=str(payload.get("text") or ""),
                    chunk_index=int(payload.get("chunk_index") or 0),
                    score=float(row.get("score") or 0.0),
                )
            )
        return chunks


def index_book(rel_path: str, store: NexusRagStore | None = None) -> int:
    """Extract chunks from a book file and index them into Qdrant."""
    s = store or NexusRagStore()
    book_file = resolve_book_file(rel_path)
    if not book_file:
        return 0

    clean_rel = rel_path.strip('"\'').lstrip("/\\")
    title = format_book_title(book_file.name)

    # Prefer EPUB if available
    epub_file = book_file.with_suffix(".epub")
    if epub_file.is_file():
        chunks = chunk_epub(epub_file, clean_rel, title)
    elif book_file.suffix.lower() == ".pdf" and book_file.is_file():
        chunks = chunk_pdf(book_file, clean_rel, title)
    else:
        return 0

    if not chunks:
        return 0

    return s.upsert_chunks(chunks)


def index_served_documents(store: NexusRagStore | None = None) -> dict[str, int]:
    """Index EPUB and PDF files under the Nexus content folders. EPUB wins over a PDF twin."""
    from .nexus_library import CONTENT_DIRS

    s = store or NexusRagStore()
    root = find_nexus_root()
    if not root:
        return {}
    results: dict[str, int] = {}
    seen_stems: set[str] = set()
    files: list[Path] = []
    for folder in CONTENT_DIRS:
        base = root / folder
        if not base.is_dir():
            continue
        files.extend(base.rglob("*.epub"))
    for folder in CONTENT_DIRS:
        base = root / folder
        if not base.is_dir():
            continue
        files.extend(base.rglob("*.pdf"))
    for book in files:
        rel = book.relative_to(root).as_posix()
        if any(part.startswith(".") for part in Path(rel).parts):
            continue
        stem_key = f"{book.parent}/{book.stem}"
        if stem_key in seen_stems:
            continue
        seen_stems.add(stem_key)
        results[rel] = index_book(rel, store=s)
    return results


def index_all_books(store: NexusRagStore | None = None) -> dict[str, int]:
    """Index all available books under 04_Books_Library in Nexus."""
    s = store or NexusRagStore()
    root = find_nexus_root()
    if not root:
        return {}

    library_dir = root / "04_Books_Library"
    if not library_dir.is_dir():
        return {}

    results: dict[str, int] = {}
    seen_stems: set[str] = set()

    # Prioritize EPUB first to avoid redundant PDF chunking when EPUB exists
    files = list(library_dir.rglob("*.epub")) + list(library_dir.rglob("*.pdf"))
    for f in files:
        rel = str(f.relative_to(root))
        stem_key = f"{f.parent}/{f.stem}"
        if stem_key in seen_stems:
            continue
        seen_stems.add(stem_key)

        count = index_book(rel, store=s)
        results[rel] = count

    return results
