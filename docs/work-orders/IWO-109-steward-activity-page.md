# IWO-109 — Steward activity page

**Status:** Complete (deployed to mac-mini 2026-10-21)  
**Priority:** P2  

**Effort:** S  
**Owner:** operator  
**Feature:** FEAT-022  
**Services / Areas:** platform

## Problem

Goals, wakes, and activity exist on authenticated routes. The lab has no page where the operator can hand the Steward a goal, read what a wake left, or pause and close a goal.

## Decision Context

- Chosen approach: a `/steward` page in the same chrome as Classroom. It reads the existing Steward routes. Goal text is written with `textContent`.
- Alternatives rejected: putting the lists inside the chat transcript. A second agent identity.
- Assumptions: loopback and the trusted tailnet can open the page the same way they open Classroom.
- Open decisions: none.

## What To Build / Fix

- `GET /steward` with a goal form, the goal list, and the activity list.
- Pause and close call the existing routes. A closed goal stays on the list without those buttons.
- A Steward link in the studio sidebar and the shared top nav.

## Expected Change Surface

- Expected: `steward.html`, `steward.js`, the page route, sidebar and top-nav links, tests.
- Tests: `tests/test_steward.py`
- Docs/status: FEAT-022, `docs/features/index.md`

## Out Of Scope

- Host deploy and a live wake on the mini
- Mail, calendar, browser history, or other new grants
- Chat inside this page

## Do NOT Change

- The See / Draft / Approval classes. The form offers only See tools, and only as checked boxes the operator can clear.
- No new privileged tool. No secret in Git. No runtime work-order row.

## Acceptance Criteria

1. `/steward` is linked from the studio sidebar and the top nav.
2. Saving a goal shows it. Pause, then close, updates the status and leaves the record.
3. Activity renders from `GET /v1/steward/activity`. An empty list says nothing has woken.
4. Goal and activity text is not assigned with `innerHTML`.
5. `./scripts/validate-repo.sh` passes.

## Validation Plan

- Automated: `python3 -m unittest tests.test_steward -v`, then `./scripts/validate-repo.sh`
- Manual: headless Chrome on loopback — save a goal, pause it, close it
- Evidence to include: unittest summary and the browser pass

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none
- **May run on Air?** Yes for unit tests and a loopback page check. Lab compose on Air is forbidden.

## Execution

- **Branch:** `iwo/109-steward-activity-page`
- **Risk tier:** P2
- **Pre-PR / pre-merge gate:** `./scripts/validate-repo.sh` and `python3 -m unittest tests.test_steward -v`
- **Depends on:** IWO-108
- **Human verification required:** Yes
- **Reviewer / approver:** operator
- **Project status record:** `docs/features/index.md`
- **Other status surfaces:** `docs/features/FEAT-022-steward.md`

## Closeout

- Verification evidence: `python3 -m unittest tests.test_steward -v` — 11 tests OK (2026-10-18). Headless Chrome on loopback saved a goal, paused it, and closed it. The record stayed, the buttons went away, and the activity list stayed empty. `./scripts/validate-repo.sh` — OK.
- Follow-ons filed: outside sources remain later grants on FEAT-022.
- Residual risks: a wake has not been watched on the mini. The desk passed headless Chrome on loopback, including a 390px width with no horizontal overflow.
- Docs/status updated: FEAT-022, index
- Status surfaces reconciled: yes
- Summary metadata reviewed: yes
- Planning-only change? No
- Host deploy performed? Yes — 2026-10-21 the desk page, script, `steward.py`, and `control_app.py` were copied to the mini and `com.ai-lab.control-plane` was restarted. `GET http://mac-mini:8088/health` returned ok. `GET /steward` served the desk. No compose, model pull, or firewall change.
