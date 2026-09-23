# FEAT-008 — Scoped research and retrieval memory

- **Status:** Specified
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
| IWO-040 | Retrieval API + citation policy | Report with sources |
| IWO-041 | Memory write gates | Audited writes only |

## Out of scope

Unrestricted crawl; Clarion production DB ingestion.

## Implementation status

| Layer | Status |
|-------|--------|
| Spec | Done |
| Code | Partial (report plan; Qdrant healthy; no retrieval API) |
| Live | Partial (Qdrant container) |
