# IWO-040 — Retrieval API + citation policy (FEAT-008)

**Status:** Complete  
**Priority:** P1  
**Effort:** M  
**Owner:** human (operator)  
**Feature:** [FEAT-008](../features/FEAT-008-research-retrieval-memory.md)  
**Services / Areas:** platform (retrieval, tools, control_app), agents/research  
**Risk tier:** P2  
**GitHub:** [#9](https://github.com/sgerhart/ai-lab/issues/9)

## Problem

Qdrant is live on the mini but personal agents have no retrieval API. Research
policy forbids fabricating citations; empty retrieval must stay empty.

## Decision Context

- Chosen approach: authenticated memory upsert/search API; `memory_search` tool
  for allowlisted agents; deterministic hash embeddings for tests and when no
  embed model is configured; optional Qdrant HTTP backend when
  `QDRANT_URL` + `QDRANT_API_KEY` are set. In-memory store for unit tests /
  when Qdrant is down.
- Alternatives rejected: require Ollama embed model pull in this IWO; add
  heavy embedding SDKs.
- Assumptions: vector size fixed at 64 for hash embeds; Qdrant collection
  created on first upsert.
- Open decisions: Ollama embed model id (follow-on when a model is authorized).

## What To Build / Fix

- `retrieval.py` — embed + MemoryStore (in-memory + Qdrant)
- `POST /v1/memory/documents`, `POST /v1/memory/search`, `GET /v1/memory/status`
- Tool `memory_search` (read-only); cite `source` + snippet; empty → honest note
- Add to research (+ lab-operations) allowed_tools
- Unit tests without live Qdrant
- Docs: FEAT-008, index, #9

## Out Of Scope

- Agent-driven memory writes (IWO-041)
- Unrestricted crawl / web fetch
- Model pull for embeddings
- Changing Qdrant compose

## Do NOT Change

- ADR 0024 (API key required for live Qdrant)
- Citation no-fabrication policy
- Secrets in Git

## Acceptance Criteria

1. Upsert then search returns the document with source in unit tests.
2. Empty search returns `matches: []` and a no-fabrication note.
3. `memory_search` tool returns the same shape.
4. No host deploy / compose change in this IWO.

## AI Lab gates

- **Creates runtime job on mac-mini?** No
- **Host deploy authorized by this IWO alone?** **No**
- **May run on Air?** Yes (unit)

## Closeout

- Verification evidence: `python3 -m unittest tests.test_retrieval -v`
- Follow-ons: IWO-041 agent memory_write gates; optional Ollama embeddings when model authorized
- Docs/status updated: FEAT-008, features index
- Host deploy performed? No
