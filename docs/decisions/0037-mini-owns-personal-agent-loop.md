# ADR 0037 — Mini owns the personal-agent loop

- **Status:** Accepted
- **Date:** 2026-09-21
- **Related:** ADR 0009, 0010, 0011, 0020; FEAT-010

## Context

AI Lab’s three-host split is clear for infrastructure, but agent *execution*
can be misread as “everything interesting waits for Studio.” The desired
product is an always-on **personal-agent platform** on the mini, with Studio as
compute/inference—not as the owner of agent lifecycle.

## Decision

1. The **Mac mini** owns: agent harness, model-driven agent loops, orchestration,
   scheduling, durable state, agent/conversation records, tool registry,
   permissions, approvals, audit, memory services, model **routing policy**,
   and the human-facing web UI/API.
2. The **Mac Studio** owns: heavy inference (Ollama/MLX), training/eval, Jupyter
   kernels, and optional isolated task workers. It does **not** own the
   authoritative work-order database or personal-agent lifecycle.
3. The **Mac Air** remains the human/development plane. It must not be required
   awake for mini-managed background agents.
4. LangGraph on the mini may call Studio (or cloud) for inference bytes; the
   **loop** still advances on the mini (ADR 0020 clarified, not replaced).
5. Deterministic `agent_plans.py` remains a test/fixture path until FEAT-010
   lands a real model/tool loop.

## Consequences

- FEAT-010 is the harness feature; FEAT-003 is Studio integration, not the
  definition of “having agents.”
- Jupyter (FEAT-006) is a separate Studio track and does not route cells through
  the harness by default.

## Alternatives considered

- Wait for Studio before any agent UX — rejected; mini can use FakeBackend and
  later local/cloud providers.
- Move authoritative state to Studio — rejected; Studio may sleep/reboot; mini
  is the always-on plane (ADR 0009).
