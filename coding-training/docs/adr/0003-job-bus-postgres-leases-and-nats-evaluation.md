# ADR 0003 — Job Bus: PostgreSQL Lease Scheduling and NATS Evaluation

- **Status:** Accepted (WO-00)
- **Date:** 2026-10-30
- **Context:** `ai-lab/coding-training/`
- **Related:** `docs/decisions/0014-postgres-qdrant-redis.md`, `0020-langgraph-orchestration.md`

## Context

The system requires reliable distribution of candidate execution jobs and training tasks between the Controller (on `mac-mini`), the Model Worker (on `mac-studio`), and the Sandbox Worker (on the Proxmox Linux VM).

The specification recommends: "prefer existing NATS; Redis only if actually needed."
However, repository reconnaissance reveals that NATS is **not currently deployed in AI Lab** (it exists only in the separate, adjacent Clarion stack). In contrast, AI Lab already has PostgreSQL 16.6 and Redis 7.4.2 running in `infrastructure/compose.yaml`, with ADR 0014 establishing PostgreSQL as the authoritative state machine and Redis as ephemeral cache/queue.

## Decision

1. **Phase 1 (Pilot & Baseline): PostgreSQL Lease-Based Job Scheduling**
   - Implement job distribution using an explicit, lease-based queue table in PostgreSQL (`execution_jobs`).
   - Workers claim jobs atomically using `SELECT ... FOR UPDATE SKIP LOCKED` with a lease expiration timestamp (`lease_expires_at`).
   - Heartbeats extend active leases. If a worker crashes or drops off, stale leases expire automatically and become eligible for bounded retries.
   - This eliminates the operational overhead of deploying and maintaining NATS JetStream for the initial prototype while guaranteeing 100% durable audit trails and crash recovery in PostgreSQL.

2. **Phase 2 (High-Throughput RL Rollouts): NATS JetStream Evaluation**
   - If reinforcement learning rollout loops require sub-millisecond, high-throughput pub/sub across dozens of parallel candidate executions that strain PostgreSQL connection pools, NATS JetStream can be added as an optional compose overlay on `mac-mini`.
   - Even if NATS is introduced for transport, PostgreSQL remains the immutable record of truth for all scored outcomes, rewards, and training runs.

3. **Redis Role:**
   - Redis may be used for fast distributed locking, rate-limiting, and short-term caching of test-bundle digests, but never as the authoritative job state.

## Consequences

- Zero new external infrastructure services are required for WO-01 through WO-06.
- All job history, retries, and worker attestations are immediately queryable via standard SQL and existing AI Lab database backup routines.
