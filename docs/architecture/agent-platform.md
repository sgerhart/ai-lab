# Agent platform

**Code:** [`platform/`](../../platform/README.md)  
**Status:** LangGraph vertical slice + FastAPI control plane are **implemented and unit-tested**. Postgres store and LangGraph checkpoints are tested against ephemeral local Postgres. Live M1/Studio processes are **not deployed**.

LangGraph orchestrates **workflow steps and resume** (ADR 0020). It does not replace PostgreSQL work-order records, tool permissions, model serving, or Studio workers.

## Separation

```text
Human / UI (M3 Air)
    |
FastAPI control plane (M1) + LangGraph
    |
    +-- Work-order intake          FastAPI
    +-- Durable task state         PostgreSQL (SQLite in tests)
    +-- Workflow + checkpoints     LangGraph (Postgres saver on M1)
    +-- Job dispatch               HTTP client → Studio worker
    +-- Tool permissions           policy.json + approvals.py
    +-- Human approvals            graph interrupt + POST /approve
    |
Studio worker (M5 Max)
    |
Isolated execution / Ollama
```

Do not add CrewAI, AutoGen, Temporal, or Celery without a new ADR.

## Vertical slice (tested)

Submit work order → persist → LangGraph → Studio worker **runs the agent plan** → pause (`awaiting_approval`) → resume → complete.

Also tested: control-plane restart using the same checkpointer; Studio unavailable leaves the work order `queued` with `studio_unavailable` (it does not vanish); a failed plan leaves the work order `failed` with `plan_failed` (it does not vanish); Postgres store + checkpoint round-trip on a throwaway local database.
