# ADR 0009 — M1 mini is the control plane

- **Status:** Accepted
- **Date:** 2026-09-20

## Context

The Studio will run heavy inference and training. If orchestration, queues, and databases live on the Studio, a restart or memory spike loses agent state. The M1 mini is always-on with 16 GB unified memory and 512 GB disk.

## Decision

The M1 Mac mini owns persistent agent state and control-plane services: PostgreSQL, Qdrant, Redis, orchestration, scheduling, model-routing *control*, health, backup orchestration.

Design for **16 GB total system memory**, not 16 GB for Docker. Default compose includes only Postgres, Redis, and Qdrant. Optional monitoring is a compose profile, off by default.

The M1 does not run large local models.

## Consequences

- Studio unavailability must queue, retry, or fail visibly.
- Backup destination cannot be the M1 itself (open: D-011).
- Docker VM size on the M1 must be capped; see ADR 0013.

## Alternatives considered

- Studio as combined control+compute — rejected; state would die with GPU load.
- MacBook as control plane — rejected; laptops sleep.
