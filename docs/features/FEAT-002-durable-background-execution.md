# FEAT-002 — Durable background execution

- **Status:** Partial (IWO-031 background worker in Git)
- **Created:** 2026-09-21
- **Owner:** human (operator)
- **GitHub issue:** [#3](https://github.com/sgerhart/ai-lab/issues/3)

## Purpose

Runtime work orders and agent runs on the mini survive Air sleep, control-plane
restarts, and Studio/provider outages. PostgreSQL is authoritative; Redis is
never the only copy of a job.

## User workflow

1. Submit a durable task (API or UI) while on the Air.
2. Close the laptop.
3. Mini continues or safely pauses (`queued` / `awaiting_approval` / `failed`).
4. Reopen UI later; retrieve result or resume approval.

## Target host(s)

| Role | Host alias | Why |
|------|------------|-----|
| SoT + harness | `mac-mini` | Always-on |
| Optional worker | `mac-studio` | Heavy steps when up |
| Client | `mac-air` | Submit/retrieve only |

## Dependencies

- FEAT-010 (agent runs), ADR 0020, 0037
- Live: PostgresStore + LangGraph checkpoints on mini

## Proposed deliverables

- Already: FastAPI, PostgresStore, checkpoints, LaunchAgent, Studio-down requeue
- IWO-006: stuck-`running` reconcile, cancel/retry safety
- IWO-031: agent runs enqueue as `queued`; in-process worker + `/v1/agent-runs/worker/tick`

## Proposed implementation work orders

| ID | Title | Depends on | Acceptance |
|----|-------|------------|------------|
| IWO-006 | Durable async recovery | IWO-005 | Air closed; result retrievable; no vanish |

## Acceptance criteria

- [x] Laptop closed; job still in Postgres (partial — today’s runtime WOs)
- [x] Studio down → `queued` + visible error
- [x] Agent-run background path same guarantees (IWO-031 enqueue + worker)
- [x] Safe retry only when idempotent / allowed (re-queues for worker)

## Out of scope

- Air as always-on queue; Clarion jobs

## Implementation status (honest)

| Layer | Status | Evidence |
|-------|--------|----------|
| Spec | Done | this file |
| Code | Partial | store + slice_graph + IWO-031 agent-run worker |
| Deploy | Partial | mini:8088 (worker on when DATABASE_URL / AI_LAB_AGENT_WORKER) |
| Live verified | Partial | submit/health from Air; worker unit-tested |
