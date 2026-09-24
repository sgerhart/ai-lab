# IWO-030 — Personal agent schedule tick (FEAT-009)

**Status:** Complete  
**Priority:** P1  
**Effort:** M  
**Owner:** human (operator)  
**Feature:** [FEAT-009](../features/FEAT-009-scheduled-personal-agents.md), [FEAT-013](../features/FEAT-013-personal-agent-studio.md)  
**Services / Areas:** platform (scheduler, agent_definitions, control_app, Studio Agents UI)  
**Risk tier:** P2  
**GitHub:** [#10](https://github.com/sgerhart/ai-lab/issues/10)

## Problem

Agent definitions store `schedule_cron` (IWO-026) but nothing fires them. FEAT-009
needs periodic personal/lab-ops runs on the mini without Celery/Temporal
(ADR 0020) and without silent remediation.

## Decision Context

- Chosen approach: authenticated `POST /v1/scheduler/tick` that matches 5-field
  cron expressions, records last fire under `~/.ai-lab/`, and starts a bounded
  agent-definition run (same path as manual Run). Operator can call tick from a
  LaunchAgent/`cron` later; this IWO does **not** install host timers.
- Alternatives rejected: Celery/Temporal; in-process background thread as the
  only trigger (harder to observe; still need an external nudge for reliability).
- Assumptions: local Studio Ollama / fake backends only for scheduled runs unless
  usage-billed is already authorized; lab-ops tools stay read-only.
- Open decisions: timezone (use host local time for cron for v1).

## What To Build / Fix

- Stdlib 5-field cron matcher (`minute hour dom month dow`)
- Schedule state file `~/.ai-lab/schedule-state.json` (never Git)
- `POST /v1/scheduler/tick` (+ `GET /v1/scheduler/status`)
- `scripts/scheduler-tick.sh` (curl helper; dry-run prints command)
- Studio Agents create form: optional cron field
- Unit tests; docs/index/FEAT-009 update

## Expected Change Surface

- Expected: new `schedule_cron.py` / `agent_scheduler.py`, `control_app.py`,
  `agents.html`, `scripts/scheduler-tick.sh`, tests, docs
- Tests: cron match + tick due/skip
- Docs/status: this IWO, FEAT-009, features index, GitHub #10

## Out Of Scope

- Installing LaunchAgent / system crontab on the mini (separate deploy auth)
- Write tools / auto-remediation
- Complex cron (seconds, `@daily` macros, TZ env beyond local)
- FEAT-002 background worker for in-flight HTTP requests

## Do NOT Change

- ADR 0020 (no Celery/Temporal)
- Deny-by-default MCP / privileged tool policy
- Secrets in Git; `0.0.0.0` binds

## Acceptance Criteria

1. Definition with `schedule_cron` matching “now” starts a run on tick (unit test).
2. Same minute does not double-fire.
3. Invalid cron is skipped with a visible error in tick result (not a 500).
4. `./scripts/validate-repo.sh` / relevant unit tests pass.
5. No host LaunchAgent installed by this IWO.

## Validation Plan

- Automated: `python3 -m unittest tests.test_agent_scheduler -v`
- Manual: create definition with cron, `POST /v1/scheduler/tick` while signed in
- Evidence: test output; tick JSON `started` / `skipped`

## AI Lab gates

- **Creates runtime job on mac-mini?** Yes (when tick runs live) — only after
  operator calls tick or installs a timer separately
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none beyond existing agent policy
- **May run on Air?** Yes (unit tests only)

## Execution

- **Branch:** main (operator backlog slice)
- **Depends on:** IWO-026
- **Human verification required:** Yes (live tick on mini optional)
- **Project status record:** `docs/features/index.md` + this file + #10

## Closeout

- Verification evidence: `python3 -m unittest tests.test_agent_scheduler -v` (8 ok)
- Follow-ons: LaunchAgent plist in Git + install auth (IWO-052); FEAT-002 async agent runs
- Residual risks: wall-clock tick must be invoked externally until host timer authorized
- Docs/status updated: FEAT-009, features index, `platform/scheduler/README.md`
- Host deploy performed? No
