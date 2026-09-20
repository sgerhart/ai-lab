# ADR 0014 — PostgreSQL, Qdrant, and Redis responsibilities

- **Status:** Accepted
- **Date:** 2026-09-20

## Context

The agent harness needs durable work orders, a queue, and vector memory. Using Redis as the only record would lose work on restart unless AOF/RDB is treated as canonical — a poor fit for structured work-order state.

## Decision

| System | Responsibility | Authoritative? |
|--------|----------------|----------------|
| **PostgreSQL** | Work orders, attempts, audit events, approval records, agent identities | Yes for those records |
| **Qdrant** | Embeddings / vector memory | Yes for vectors; metadata keys point at Postgres IDs |
| **Redis** | Queue, ephemeral cache, rate limits | No. Restart recovery replays `queued`/`running` from Postgres |

Work-order state machine lives in the platform code and in Postgres, not in Redis keys alone.

## Consequences

- Backup must dump Postgres (and Qdrant storage) to a **non-M1** target.
- Redis persistence can be enabled as a cache convenience, not as the recovery story.
- Orchestrator start must reconcile in-flight rows.

## Alternatives considered

- Redis-only work orders — rejected.
- SQLite on the M1 host filesystem — acceptable for tests; not the deployed control plane.
