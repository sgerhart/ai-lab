# ADR 0006 — Phase-gated delivery

- **Status:** Accepted
- **Date:** 2026-09-19
- **Phase:** 0

## Context

Building serving, agents, and observability in one pass produces undebuggable systems and skips hardening. The current work order authorizes Phase 0 only.

## Decision

Work proceeds in numbered phases with a work order per phase. An agent must stop at phase completion, report, and wait for authorization before starting the next phase.

Phase 0 is repository foundation. It does not provision hosts, pull models, or change live listeners.

## Consequences

- Recommended next work order is WO-001 (Phase 1), not an implied continuation.
- Live hardening of Ollama's bind address waits for Phase 1 even though it is already a known finding.
