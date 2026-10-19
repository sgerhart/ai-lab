# IWO-106 — Classroom voice and whiteboard

**Status:** Review  
**Priority:** P3  
**Effort:** M  
**Owner:** operator  
**Feature:** FEAT-021  
**Services / Areas:** platform

## Problem

The lab can chat, study a library, and draft agents. It has no class: a topic, a lesson plan, a spoken explanation, and a whiteboard the instructor draws on while teaching. Questions and a raised hand have nowhere to go.

## Decision Context

- Chosen approach: a Classroom section at `/classroom`. The local model writes a JSON lesson. The browser speaks it and draws an allow-listed set of board marks. If the model reply is not a lesson, the classroom outline still runs.
- Alternatives rejected: a separate speech server, a video avatar, and putting the class inside the chat transcript.
- Assumptions: the operator's browser can speak. A local model may be unavailable.
- Open decisions: none that block this slice. A neural voice and saved transcripts are follow-ons.

## What To Build / Fix

- `platform/src/ai_lab_platform/classroom.py` builds and checks lesson plans and answers.
- `POST /v1/classroom/lessons` and `POST /v1/classroom/questions`, both authenticated, local model only.
- `GET /classroom` with a lesson plan, whiteboard, raise-hand control, and question box.
- A Classroom link in the lab sidebar and the shared top nav.

## Expected Change Surface

- Expected: classroom module, page, script, two API routes, nav links, tests, this feature record.
- Tests: `tests/test_classroom.py`
- Docs/status: `docs/features/FEAT-021-classroom.md`, `docs/features/index.md`

## Out Of Scope

- Host deploy, control-plane restart, model pulls
- Server-side text-to-speech, avatars, multi-student rooms, saved transcripts

## Do NOT Change

- No secrets in Git.
- No usage-billed model as a fallback.
- No `eval` of model output and no HTML from lesson text.
- No new bind address. No runtime work-order rows.

## Acceptance Criteria

1. Naming a topic returns a lesson with objectives, spoken sections, and board marks.
2. A question returns speech and board marks.
3. Board operations outside the allow-list are dropped. Markup in text is stripped.
4. The lesson request uses the local backend only.
5. `/classroom` shows the board, raise hand, and ask controls, and the sidebar links to it.
6. `python3 -m unittest tests.test_classroom` passes.

## Validation Plan

- Automated: `python3 -m unittest tests.test_classroom -v`
- Manual: open `/classroom`, start a topic, confirm the browser speaks and the board draws. Not done in this change.
- Evidence to include: unit-test result. Browser pass remains for the operator.

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none
- **May run on Air?** No — this does not start lab compose. The page is served by the control plane.

## Execution

- **Branch:** current workspace
- **Risk tier:** P3
- **Pre-PR / pre-merge gate:** `python3 -m unittest tests.test_classroom -v`
- **Depends on:** FEAT-011 local model router
- **Human verification required:** Yes — spoken playback and drawing in a browser
- **Reviewer / approver:** operator
- **Project status record:** `docs/features/index.md`
- **Other status surfaces:** `docs/features/FEAT-021-classroom.md`

## Closeout

- Verification evidence: `python3 -m unittest tests.test_classroom -v` — 12 tests OK. 2026-10-17: files copied to the mini and `com.ai-lab.control-plane` restarted. `GET http://mac-mini:8088/classroom` served the board, raise-hand, and ask controls. `POST /v1/classroom/lessons` for photosynthesis returned a local-model plan (`source=model`, 5 segments). Browser speech was not watched in a browser session.
- Follow-ons filed: none. A neural voice, saved transcripts, and a live browser pass are open and not separate work orders yet.
- Residual risks: browser speech can be blocked until the operator clicks Voice on, or missing in a browser without a speech engine. The captions and the board still advance. The lesson is not confirmed in a live browser. 2026-10-17 follow-up: the board is one composed page per beat, and Pause stops the voice and the pen. Drawing quality is still waiting on a live class.
- Docs/status updated: `docs/features/FEAT-021-classroom.md`, `docs/features/index.md`
- Status surfaces reconciled: index lists FEAT-021 and IWO-106
- Summary metadata reviewed: yes
- Planning-only change? No
- Host deploy performed? Yes — classroom files copied to the mini checkout and the control-plane LaunchAgent restarted. No compose, model pull, or firewall change.
