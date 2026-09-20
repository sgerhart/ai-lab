# ADR 0011 — M3 Air is the human / development plane

- **Status:** Accepted
- **Date:** 2026-09-20

## Context

Confirmed: MacBook Air, Apple M3, 512 GB internal storage. Unified memory is **not attested by the owner**. This workspace host is an Apple M3 Mac; `sysctl hw.memsize` reported 16 GB on 2026-09-19. That observation is recorded as unconfirmed inventory, not as a design input that sizes services.

## Decision

The M3 Air is for IDE, Git/GitHub, SSH administration, dashboards, human approvals, Jupyter *client*, and review. It must not host essential always-on services. Ollama currently running on this laptop is opportunistic, not the lab inference plane.

Do not invent RAM in committed "confirmed hardware" tables. Use "unconfirmed (16 GB observed on workspace host, 2026-09-19)" until the owner attests.

## Consequences

- Dashboards may be unreachable when the lid is closed. That is acceptable.
- Finding F-003 (Ollama `*:11434` on this laptop) is a workstation hygiene issue, not the Studio serving design.

## Alternatives considered

- Air as control plane — rejected (sleep).
- Air as inference plane — rejected (capacity and sleep).
