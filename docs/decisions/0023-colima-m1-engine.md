# ADR 0023 — Colima as the initial M1 container engine

- **Status:** Accepted
- **Date:** 2026-09-21
- **Supersedes:** open decision D-013
- **Related:** ADR 0013

## Context

The M1 mini has 16 GB. An uncapped Docker Desktop VM can starve Postgres. The m1-mini Brewfile already lists Colima, not Docker Desktop.

## Decision

**Colima** is the initial engine on `m1-mini`. Suggested cap at first `up` (not applied until authorized): 2 CPUs, 3 GB RAM, 40 GB disk. Docker Desktop is not forbidden forever; switching requires a new ADR and a measured RAM budget.

## Consequences

- `hosts/m1-mini/setup.sh --apply` installs Colima + Docker CLI (when authorized).
- Compose remains the service definition (ADR 0013).
