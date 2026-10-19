# IWO-105 — Knowledge Nexus Qdrant Book RAG Indexer & Semantic Search

**Status:** Complete  
**Priority:** P2  
**Effort:** M  
**Owner:** Steven Gerhart  
**Feature:** FEAT-008  
**Services / Areas:** platform, tests, docs

## Problem

Currently, the Nexus Study Copilot relies on regex and term-frequency string matching against on-disk EPUB and PDF files. While this works well for exact keywords and known chapter queries, it cannot perform sub-millisecond semantic search or cross-book knowledge retrieval, and it rescans files on every chat turn.

Qdrant is already deployed and active on the M1 mini host (`127.0.0.1:6333`, collection `ai_lab_memory`), authenticated via API key per ADR 0024. A dedicated collection for Knowledge Nexus library books will enable persistent vector storage, fast similarity search, and hybrid retrieval.

## Decision Context

- Chosen approach: Create a dedicated Qdrant collection `nexus_books`. Implement semantic chunking for EPUB and PDF documents. Upgraded to high-performance neural transformer embeddings via `BAAI/bge-small-en-v1.5` (384-dimensional dense vectors using ONNX Runtime / `fastembed`), with fallback to normalized `hash_embed` (64 dimensions) when fastembed is unavailable.
- Alternatives rejected:
  - Relying exclusively on raw disk regex scans (slow on multi-megabyte PDFs, misses conceptual synonyms).
  - Heavy GPU embedding servers that steal VRAM from the LLM on Mac Studio.
- Assumptions:
  - Qdrant is available via `QDRANT_URL` and `QDRANT_API_KEY`.
  - If Qdrant is unreachable or empty, retrieval seamlessly falls back to direct on-disk extraction.

## What To Build / Fix

1. `platform/src/ai_lab_platform/nexus_rag.py`:
   - Chapter-aware chunking for EPUB and PDF.
   - `ensure_nexus_collection()` to initialize `nexus_books` in Qdrant.
   - `index_book(rel_path)` to chunk and upsert vectors + metadata payloads to Qdrant.
   - `search_book_chunks(query, rel_path=None, limit=4)` to search Qdrant for matching chunks.
2. `platform/src/ai_lab_platform/nexus_study.py`:
   - Query Qdrant vector index first. If matching chunks exceed threshold, use them as grounded excerpts. Fall back to on-disk scanner if Qdrant has no match.
3. `scripts/index-nexus-books.py`:
   - Operator script to index specific books or all books into Qdrant.
4. `tests/test_nexus_rag.py`:
   - Unit tests verifying chunking, vector generation, collection initialization, and fallback logic.

## Expected Change Surface

- `platform/src/ai_lab_platform/nexus_rag.py` (new)
- `platform/src/ai_lab_platform/nexus_study.py` (modified)
- `scripts/index-nexus-books.py` (new)
- `tests/test_nexus_rag.py` (new)

## Out Of Scope

- Modifying host daemon configurations or pulling unapproved model weights.
- Replacing the Postgres conversation store.

## Do NOT Change

- ADR 0024 API key enforcement on Qdrant.
- Existing `ai_lab_memory` collection.
- Local fallback behavior in Study Mode.

## Acceptance Criteria

- [x] `nexus_books` collection can be created and queried in Qdrant.
- [x] EPUB and PDF books can be chunked and indexed with chapter metadata.
- [x] Study Mode transparently queries Qdrant and falls back to disk scan if empty.
- [x] All unit tests pass and `./scripts/validate-repo.sh` passes.
