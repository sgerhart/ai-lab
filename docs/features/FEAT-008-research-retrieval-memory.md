# FEAT-008 — Scoped research and retrieval memory

- **Status:** Partial (IWO-040/041 + IWO-053 Qdrant live on mini)
- **Created:** 2026-09-21
- **Owner:** human (operator)
- **GitHub issue:** [#9](https://github.com/sgerhart/ai-lab/issues/9)

## Purpose

Sourced research artifacts and scoped retrieval from Qdrant for personal agents—
after the mini loop (FEAT-010) exists. Memory writes are gated and audited.

## Dependencies

FEAT-010, FEAT-003; Qdrant live on mini.

## Proposed IWOs

| ID | Title | Acceptance |
|----|-------|------------|
| [IWO-040](../work-orders/IWO-040-retrieval-api.md) | Retrieval API + citation policy | Search returns sources; empty stays empty |
| [IWO-041](../work-orders/IWO-041-memory-write-gates.md) | Memory write gates (agent tool) | Audited writes only |

## Out of scope

Unrestricted crawl; Clarion production DB ingestion.

## Implementation status

| Layer | Status |
|-------|--------|
| Spec | Done |
| Code | Partial — `/v1/memory/*`, `memory_search`, gated `memory_write` (IWO-040/041) |
| Live | Qdrant wired on mini 2026-09-24 (`backend=qdrant`); hash embeds |
