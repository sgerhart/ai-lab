# IWO-107 — Steward access manifest and standing goals

**Status:** Complete (unit-tested; deployed to mac-mini 2026-10-21)  
**Priority:** P1  

**Effort:** M  
**Owner:** operator  
**Feature:** FEAT-022  
**Services / Areas:** platform

## Problem

The personal agent can chat, read the memory vault and notes, search Nexus, and file reports. It runs when the operator sends a message or when a saved cron fires. It has no standing responsibility, and it has no written boundary for how much of the operator's work an unattended wake may see.

FEAT-022 wants that boundary before any wake calls a model.

## Decision Context

- Chosen approach: one manifest module and a goal file on the operator's mini. Goals name a responsibility and a subset of the See list. The existing scheduler tick marks a due goal. It does not enqueue a model run.
- Alternatives rejected: a new agent id beside `personal`. A wake that calls Studio in this order, before the allow-list is tested. Granting the home directory, mail, or secrets because the operator wants broad awareness.
- Assumptions: `agents/personal/policy.json` remains the ceiling. The manifest only narrows tools for a wake. Goal JSON under `~/.ai-lab/` is acceptable operator state, as schedule state already is.
- Open decisions: the product label may change from Steward before this order is accepted. The agent id does not change.

## What To Build / Fix

- `platform/src/ai_lab_platform/steward.py`
  - Access classes `see`, `draft`, `approval`, `never`, matching FEAT-022.
  - Default manifest built from the personal policy's current tools. Unknown tool names are `never`.
  - `background_tools(goal)` returns only See tools named on that goal. Draft, Approval, and Never are absent.
  - Goal records: id, title, intent, status (`active`, `paused`, `done`), wake cron, allowed see-tools, last marked due. Stored in a JSON file. Tests pass a temp path. Mode `0600` on the file.
  - Create, list, pause, and close. Pause and close do not delete the record.
- Authenticated routes on the control plane:
  - `GET /v1/steward/access` returns the manifest classes.
  - `GET /v1/steward/goals` and `POST /v1/steward/goals`.
  - `POST /v1/steward/goals/{id}/pause` and `POST /v1/steward/goals/{id}/close`.
- Scheduler tick: for each active goal whose cron matches this minute, set `last_due_at` once per local minute. Do not call the model router and do not insert an `agent_runs` row.

## Expected Change Surface

- Expected: `steward.py`, scheduler tick hook, control-plane routes, tests, this feature's status line.
- Tests: `tests/test_steward.py`
- Docs/status: `docs/features/FEAT-022-steward.md`, `docs/features/index.md`

## Out Of Scope

- Enqueueing or running a model loop for a due goal (IWO-108)
- Activity UI (IWO-109)
- Mail, calendar, browser, home directory, classroom transcripts, computer control
- New tools, policy edits that add tools, secret reads
- Host deploy and control-plane restart

## Do NOT Change

- `personal` stays one agent. Do not add a `steward` policy file.
- ADR 0018 gates stay. This order adds no privileged tool.
- No secrets in Git. No `0.0.0.0` bind. No runtime work-order rows.
- No silent cloud-model fallback.
- Schedule state and the memory vault format stay as they are.

## Acceptance Criteria

1. Creating a goal and listing it returns the title, intent, status, and see-tools.
2. A goal that names `vault_write`, `schedule_create`, `consult_frontier`, or an unknown tool is rejected, or those names are dropped and the stored goal's background list does not contain them. The test shows which rule shipped.
3. `background_tools` for a valid goal is a subset of the See class and is disjoint from Draft and Approval.
4. One scheduler tick marks a due active goal once. A second tick in the same local minute does not mark it again. No model function is called.
5. Paused and closed goals are not marked due.
6. `./scripts/validate-repo.sh` passes.

## Validation Plan

- Automated: `python3 -m unittest tests.test_steward -v`, then `./scripts/validate-repo.sh`
- Manual: none on a host. This order does not deploy.
- Evidence to include: unittest summary

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none
- **May run on Air?** Yes for unit tests. Lab compose on Air is forbidden.

## Execution

- **Branch:** `iwo/107-steward-access-and-goals`
- **Risk tier:** P1
- **Pre-PR / pre-merge gate:** `./scripts/validate-repo.sh` and `python3 -m unittest tests.test_steward -v`
- **Depends on:** FEAT-010, FEAT-009, IWO-030
- **Human verification required:** Yes
- **Reviewer / approver:** operator
- **Project status record:** `docs/features/index.md`
- **Other status surfaces:** `docs/features/FEAT-022-steward.md`

## Closeout

- Verification evidence: `python3 -m unittest tests.test_steward tests.test_agent_scheduler -v` — 17 tests OK (2026-10-18). `./scripts/validate-repo.sh` — OK. Rule shipped for acceptance 2: create rejects the goal and stores nothing.
- Follow-ons filed: IWO-108 (read-only wake) and IWO-109 (activity UI) remain proposed on FEAT-022. Not separate files yet.
- Residual risks: goal records are a JSON file on the mini, not Postgres. A due mark does not start a run. The operator has not exercised the routes on the live control plane.
- Docs/status updated: FEAT-022, `docs/features/index.md`
- Status surfaces reconciled: index row set to Review
- Summary metadata reviewed: yes
- Planning-only change? No
- Host deploy performed? No
