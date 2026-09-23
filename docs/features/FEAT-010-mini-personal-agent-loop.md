# FEAT-010 — Mini personal-agent loop and harness

- **Status:** Partial (live Ollama tool loop — IWO-020)
- **Created:** 2026-09-21
- **Priority:** Core platform (mini-first)
- **Owner:** human (operator)
- **GitHub issue:** [#11](https://github.com/sgerhart/ai-lab/issues/11)

## Purpose

Make the Mac mini an **always-on personal-agent platform**: receive messages and
authorized tasks, run a **model-driven** think→tool→observe loop under
permissions and budgets, persist conversations and runs in PostgreSQL, and
expose them to a private UI—without requiring the Air to stay awake.

This is **not** primarily an autonomous coding factory. Coding agents (FEAT-007)
are optional workloads on this harness. Studio inference (FEAT-003) and Jupyter
(FEAT-006) remain compute-plane concerns.

**Honesty:** Existing `agent_plans.py` fixed plans remain a test fixture.
The model-driven loop is live against Studio Ollama for `lab-operations`
(IWO-020). Cloud adapters exist but stay gated (IWO-021).

## Agent loop (normative)

1. Receive user message, scheduled event, or authorized task.
2. Load agent profile and permitted context.
3. Select configured model/provider (FEAT-011).
4. Ask the model for the next response or structured tool request.
5. Validate against tool schema and per-agent permissions.
6. Execute an allowed tool, or pause for human approval of that **action**.
7. Store observation, tool trace, state, and usage.
8. Feed the result back to the model.
9. Continue until completion, stop condition, failure, cancellation, or
   step/time/token/cost budget exhaustion.

The **loop and harness run on the mini**. Inference may be Studio Ollama/MLX,
an optional small mini model, or an authorized cloud API.

## User workflow

1. From Air browser (Tailscale), open the private mini UI (FEAT-004).
2. Select an agent (start: read-only `lab-operations`) and an available model.
3. Chat ordinarily **or** submit a durable background task (runtime WO).
4. Observe tool steps; approve/deny a specific proposed action when gated.
5. Close the Air; later reopen and retrieve the completed (or failed) result.

## Target host(s)

| Role | Host alias | Why |
|------|------------|-----|
| Harness / SoT / UI API | `mac-mini` | Always-on control + agent plane |
| Inference (optional remote) | `mac-studio` | Heavy models (FEAT-003/011) |
| Human client | `mac-air` | Browser / IDE; need not stay awake |

## Dependencies

- Features: FEAT-002 (durable exec), FEAT-004 (UI), FEAT-011 (providers)
- ADRs: 0009, 0016, 0018, 0020, **0036**, **0037**, **0038**
- Live today: FastAPI + PostgresStore on mini; Studio Ollama for chat + tool loop (IWO-019/020)

## Proposed deliverables

- Conversation + agent-run contract (Postgres), distinct from chat-only turns
- Model router interface (FEAT-011)
- Bounded LangGraph model/tool loop on mini
- Tool permission + action-level approval
- Usage/budget fields; redacted traces
- Tests: denial, approval interrupt, provider-down recoverable failure, FakeBackend loop

## Proposed implementation work orders

| ID | Title | Depends on | Acceptance (sketch) |
|----|-------|------------|---------------------|
| [IWO-002](../work-orders/IWO-002-agent-run-conversation-contract.md) | Agent-run / conversation contract | IWO-001 | Schema + API + unit tests; FakeBackend only |
| [IWO-003](../work-orders/IWO-003-authenticated-agent-ui.md) | Authenticated chat UI shell | IWO-002 | Token auth; chat + status; Tailscale/loopback |
| [IWO-004](../work-orders/IWO-004-model-router.md) | Model router + billing classes | IWO-002, ADR 0038 | Fake + disabled cloud stubs; UI labels |
| [IWO-005](../work-orders/IWO-005-bounded-model-tool-loop.md) | Bounded LangGraph model/tool loop | IWO-002–004 | ≥2 model/tool steps; lab-ops read-only |
| [IWO-006](../work-orders/IWO-006-durable-async-recovery.md) | Async recovery / cancel / safe retry | IWO-005, FEAT-002 | Air closed; result retrievable |
| [IWO-007](../work-orders/IWO-007-tool-action-approvals.md) | Action-level approval UX | IWO-003, IWO-005 | Unapproved tool stops at gate |
| [IWO-020](../work-orders/IWO-020-live-ollama-agent-loop.md) | Live Studio Ollama tool loop | IWO-005, IWO-019 | health_read→FINAL on mini |

## Acceptance criteria

- [x] Loop defined and implemented on mini (not only deterministic plans)
- [x] Chat ≠ forced runtime WO; background tasks remain durable
- [x] Unapproved privileged tool stops at human gate
- [x] Provider/Studio unavailable → recoverable or visible fail (not vanish)
- [ ] First E2E: Air UI → read-only agent → ≥2 real model/tool steps → close Air → retrieve result
- [x] No new privileged tools without ADR + policy change

## Out of scope

- Autonomously coding the lab or product repos (FEAT-007)
- Routing notebook cells through the harness (FEAT-006)
- Clarion / factory orchestration inside this repo
- Chargeable live cloud calls without separate owner authorization

## Implementation status (honest)

| Layer | Status | Evidence |
|-------|--------|----------|
| Spec in Git | Done (this file) | planning PR |
| Code | Partial — IWO-002–007 + IWO-020 live Ollama loop | `agent_loop.py`, `/agents` |
| Host deploy | Control plane live; Studio Ollama wired | mini:8088 |
| Live verified | Yes — Studio Ollama tool loop (`health_read`→FINAL) | 2026-09-23 |

## Notes

See [PLAN-mini-first.md](PLAN-mini-first.md) for dependency order.
