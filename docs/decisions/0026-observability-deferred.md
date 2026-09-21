# ADR 0026 — Observability stack deferred

- **Status:** Accepted
- **Date:** 2026-09-21
- **Supersedes:** open decision D-010 for the *initial* lab

## Context

The M1 has 16 GB. Prometheus/Grafana/Loki on the same host as Postgres is an easy OOM. Work-order status and attempt history already exist.

## Decision

Do **not** enable an observability compose profile until RAM is measured on a running M1 stack and a new ADR names the tools. First telemetry is work-order rows + `audit_events`.

## Consequences

- `infrastructure/observability/` remains a README, not a second stack.
- D-010 is deferred, not “never”.
