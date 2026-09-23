# Agent platform

**Code:** [`platform/`](../../platform/README.md)  
**Status:** LangGraph vertical slice + FastAPI control plane are **implemented, unit-tested, and running on `mac-mini:8088`**. Studio worker is **not** deployed. Live restore drill is **not** done.

LangGraph orchestrates **workflow steps and resume** (ADR 0020). It does not replace PostgreSQL work-order records, tool permissions, model serving, or Studio workers.

**Forward direction (ADR 0037 / FEAT-010):** the mini owns the **personal-agent loop**
(model → tool validate → execute/approve → observe). Studio supplies inference
and heavy workers. Deterministic `agent_plans.py` is a fixture until the
model-driven loop lands—not proof that loop exists.

## Separation

```text
Human / UI (M3 Air)
    |
FastAPI control plane (M1) + LangGraph agent loop (FEAT-010)
    |
    +-- Conversations / agent runs   PostgreSQL
    +-- Work-order intake            FastAPI
    +-- Durable task state           PostgreSQL (SQLite in tests)
    +-- Workflow + checkpoints       LangGraph (Postgres saver on M1)
    +-- Model router                 FEAT-011 (local / API; cloud disabled default)
    +-- Job dispatch                 HTTP → Studio worker / Ollama (optional)
    +-- Tool permissions             policy.json + approvals.py
    +-- Human approvals              graph interrupt + UI/API (action-level)
    |
Studio (M5 Max)
    |
Ollama / MLX / Jupyter / optional isolated workers
```

Do not add CrewAI, AutoGen, Temporal, or Celery without a new ADR.

## Vertical slice (tested today)

Submit work order → persist → LangGraph → Studio worker **runs the agent plan** → pause (`awaiting_approval`) → resume → complete.

Also tested: control-plane restart using the same checkpointer; Studio unavailable leaves the work order `queued` with `studio_unavailable` (it does not vanish); a failed plan leaves the work order `failed` with `plan_failed` (it does not vanish); Postgres store + checkpoint round-trip on a throwaway local database.

Planned E2E (FEAT-010): Air UI → read-only personal agent → ≥2 model/tool steps → close Air → retrieve result.
