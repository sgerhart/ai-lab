# ADR 0011 — M3 Air is the human / development plane

- **Status:** Accepted
- **Date:** 2026-09-20

## Context

Confirmed: MacBook Air, Apple M3, 512 GB internal storage. Unified memory is **16 GB** (attested ADR 0031; also observed via `sysctl` on 2026-09-19).

## Decision

The M3 Air is for IDE, Git/GitHub, SSH administration, dashboards, human approvals, Jupyter *client*, and review. It must not host essential always-on services. Ollama on this laptop is opportunistic, not the lab inference plane (ADR 0029).

## Consequences

- Dashboards may be unreachable when the lid is closed. That is acceptable.
- Finding F-003 (Ollama `*:11434` on this laptop) is an accepted workstation risk (ADR 0029), not the Studio serving design.

## Alternatives considered

- Air as control plane — rejected (sleep).
- Air as inference plane — rejected (capacity and sleep).
