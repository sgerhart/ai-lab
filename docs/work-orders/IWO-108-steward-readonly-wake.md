# IWO-108 — Steward read-only wake

**Status:** Complete (unit-tested; deployed to mac-mini 2026-10-21)  
**Priority:** P1  

**Effort:** M  
**Owner:** operator  
**Feature:** FEAT-022  
**Services / Areas:** platform

## Problem

IWO-107 stores a standing goal and marks it due. Nothing is queued, so the personal agent still does not look at the goal between conversations.

## Decision Context

- Chosen approach: the scheduler tick enqueues one `personal` run for each goal it has just marked due. The run carries `steward_goal_id` and a tool ceiling. The loop may call only See tools on that ceiling. An activity entry records the queued run, and the worker updates that entry when the run finishes.
- Alternatives rejected: calling the model inside the tick. Letting the wake use the full personal policy, which includes draft and approval tools.
- Assumptions: the existing background worker drains the queued run. Studio Ollama is the backend named on the run. This order does not start that model in tests.
- Open decisions: none that block this slice. The activity page is IWO-109.

## What To Build / Fix

- `wake_due` marks due goals and enqueues one local, bounded run per newly marked goal.
- The run's ceiling is `background_tools`. Draft, approval, unknown, and MCP tools are absent.
- `step_agent_run` denies any tool outside that ceiling when `steward_goal_id` is set, and the wake prompt does not offer write or frontier tools.
- Activity entries live in `activity.json` beside the goals file, mode `0600`.
- `GET /v1/steward/activity` lists them. The worker writes the finished status and a short note.

## Expected Change Surface

- Expected: `steward.py`, `agent_loop.py`, `conversation.py` (`tool_ceiling`, `steward_goal_id`), `agent_worker.py`, control-plane tick and activity route, tests.
- Tests: `tests/test_steward.py`
- Docs/status: FEAT-022, `docs/features/index.md`

## Out Of Scope

- A lab page for goals and activity (IWO-109)
- Mail, calendar, browser, home directory, computer control
- Host deploy and a live model call

## Do NOT Change

- Ordinary chats keep the full personal tool list. A run with an empty `steward_goal_id` is unchanged.
- No new privileged tool. No secret in Git. No runtime work-order row.
- No silent cloud-model fallback. Wake runs are billing class `local`.

## Acceptance Criteria

1. One tick enqueues one queued personal run for a due goal and writes an activity entry. A second tick in the same minute does not enqueue another.
2. The queued run's tool ceiling is the goal's See tools. Draft and approval names are absent.
3. A wake that calls `vault_write` is denied and does not write. The wake prompt does not list that tool.
4. `./scripts/validate-repo.sh` passes.

## Validation Plan

- Automated: `python3 -m unittest tests.test_steward tests.test_agent_loop tests.test_agent_worker -v`, then `./scripts/validate-repo.sh`
- Manual: none on a host
- Evidence to include: unittest summary

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none
- **May run on Air?** Yes for unit tests. Lab compose on Air is forbidden.

## Execution

- **Branch:** `iwo/108-steward-readonly-wake`
- **Risk tier:** P1
- **Pre-PR / pre-merge gate:** `./scripts/validate-repo.sh` and the unittest command above
- **Depends on:** IWO-107
- **Human verification required:** Yes
- **Reviewer / approver:** operator
- **Project status record:** `docs/features/index.md`
- **Other status surfaces:** `docs/features/FEAT-022-steward.md`

## Closeout

- Verification evidence: `python3 -m unittest tests.test_steward tests.test_agent_loop tests.test_agent_worker -v` — 40 tests OK (2026-10-18). `./scripts/validate-repo.sh` — OK.
- Follow-ons filed: IWO-109 remains proposed on FEAT-022.
- Residual risks: the queued run waits for the control-plane worker and Studio Ollama. That path is not exercised live. Activity completion uses the default goals path on the worker, which is correct on the mini and is not what the unit test's temp directory uses.
- Docs/status updated: FEAT-022, index
- Status surfaces reconciled: yes
- Summary metadata reviewed: yes
- Planning-only change? No
- Host deploy performed? No
