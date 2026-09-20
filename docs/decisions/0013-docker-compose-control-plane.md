# ADR 0013 — Docker Compose for initial control-plane services

- **Status:** Accepted
- **Date:** 2026-09-20

## Context

PostgreSQL, Redis, and Qdrant need pinned images, volumes, healthchecks, and a single start/stop interface on the M1. Kubernetes is too much for three Macs.

Docker Desktop on a 16 GB M1 can consume several GB for the VM before any container starts. That is incompatible with "design for 16 GB system memory" unless the VM is capped.

## Decision

Use **Docker Compose** for the initial control-plane data services. Pin image tags. Default bind `127.0.0.1`. Resource limits are declared on each service.

**Container engine on the M1 is not a final ADR.** Prefer Colima with a small VM (suggested 3 GB / 2 CPUs) over an uncapped Docker Desktop. Record the engine actually installed in `hosts/m1-mini/` at bootstrap. See open decision D-013.

Compose files in this repo are **code-complete, not deployed**. `docker compose up` is unauthorized until a human says so.

## Consequences

- Monitoring is a compose profile (`observability`), off by default.
- Studio ML workloads run natively (Ollama, uv envs), not in this compose file.
- `deploy.resources` in Compose is advisory depending on engine; `mem_limit` is set as well.

## Alternatives considered

- Native Homebrew postgres/redis — harder to pin and snapshot.
- Kubernetes / Nomad — rejected for now.
- All services on Studio — rejected (ADR 0009).
