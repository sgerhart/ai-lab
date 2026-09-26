# ADR 0029 — Air Ollama wildcard bind is accepted workstation risk

- **Status:** Accepted
- **Date:** 2026-09-21
- **Supersedes:** open decision D-009

## Context

Finding F-003: Ollama on the M3 Air listens on `*:11434`. That is not the Studio serving design (ADR 0019). The owner accepted the current Air bind.

## Decision

Leave the **Air** Ollama listener as-is. It is opportunistic workstation inference, not the lab inference plane.

**Studio** Ollama listens on all interfaces so the LAN and the tailnet can both reach it ([ADR 0041](0041-studio-ollama-lan-and-tailscale.md)).

## Consequences

- F-003 is an accepted risk on the human plane, not a deploy blocker.
- Lab clients must not use the Air as `OLLAMA_HOST`.
