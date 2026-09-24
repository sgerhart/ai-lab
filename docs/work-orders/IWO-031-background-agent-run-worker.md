# IWO-031 — Background agent-run worker (FEAT-002)

**Status:** Complete  
**Priority:** P1  
**Effort:** M  
**Owner:** human (operator)  
**Feature:** [FEAT-002](../features/FEAT-002-durable-background-execution.md), [FEAT-010](../features/FEAT-010-mini-personal-agent-loop.md)  
**Services / Areas:** platform (agent_worker, agent_loop, control_app, Studio Runs)  
**Risk tier:** P2  
**GitHub:** [#3](https://github.com/sgerhart/ai-lab/issues/3)

## Problem

`execute=true` and agent-definition runs call `run_until_idle` inside the HTTP
request. Closing the Air (or a proxy timeout) can cut a long Ollama loop even
though the run row exists. FEAT-002 needs: enqueue → mini worker continues →
retrieve later.

## Decision Context

- Chosen approach: persist `queued` runs and drain them via an in-process worker
  thread (when `AI_LAB_AGENT_WORKER=1` / DATABASE_URL) plus
  `POST /v1/agent-runs/worker/tick` for tests and ops. No Celery/Temporal
  (ADR 0020).
- Alternatives rejected: only LaunchAgent curl (still need enqueue semantics);
  always-blocking HTTP (status quo).
- Assumptions: one run at a time in the worker (Ollama contention).
- Open decisions: multi-worker concurrency later.

## What To Build / Fix

- `agent_worker.drain_queued_runs`
- Enqueue-only on `execute=true` / definition runs / scheduler starts
- Control-plane lifespan worker thread (env-gated)
- Studio Run UI polls while `queued` / `running`
- Tests + FEAT-002 / index update

## Out Of Scope

- Studio isolated HTTP worker host
- Changing LangGraph work-order slice
- Host LaunchAgent install

## Do NOT Change

- ADR 0020; secrets; bind defaults; approval semantics (approve may still step)

## Acceptance Criteria

1. Create run with `execute=true` returns `queued` without waiting for FINAL.
2. Worker tick (or in-process worker) advances it to a terminal / awaiting state.
3. Unit tests cover enqueue + drain.
4. No host mutate.

## AI Lab gates

- **Creates runtime job on mac-mini?** Yes when live worker drains
- **Host deploy authorized by this IWO alone?** **No**
- **May run on Air?** Yes (unit)

## Closeout

- Verification evidence: `python3 -m unittest tests.test_agent_worker tests.test_agent_loop.MiniApiLoopTests -v`
- Follow-ons: multi-run concurrency; stuck-running auto-reconcile in worker loop
- Docs/status updated: FEAT-002, features index
- Host deploy performed? No
