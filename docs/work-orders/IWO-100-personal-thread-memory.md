# IWO-100 — Personal chat remembers the thread

**Status:** Complete (unit; not deployed)
**Priority:** P2
**Effort:** S
**Owner:** human (operator)
**Feature:** [FEAT-010](../features/FEAT-010-mini-personal-agent-loop.md)
**Services / Areas:** platform (personal agent loop)
**Risk tier:** P2

## Problem

Each personal send starts from that question alone. A follow-up in the same
chat cannot see the previous question or answer. Ordinary chat already keeps
its own transcript. The personal loop did not.

## Decision Context

- Chosen approach: before a personal run, include up to eight earlier user and
  assistant lines from that conversation. The line that matches the current
  question is left off, so it is not stated twice. Each line is capped, and the
  block is capped. Lab and other agents get an empty history.
- Alternatives rejected: putting the transcript into the memory vault on every
  turn. Switching ordinary Send onto the tool loop.
- Assumptions: the user line is stored before the run is queued, which is what
  the studio Personal agent button does.
- Open decisions: none in this slice.

## What To Build / Fix

- `earlier_turns` and `conversation_history` on the agent loop.
- The worker and the single-run tick pass that history into a personal run.

## Expected Change Surface

- Expected: `agent_loop.py`, `agent_worker.py`, `control_app.py`
- Tests: `tests/test_personal_turns.py`
- Docs/status: this file, `docs/features/index.md`, FEAT-010, agent catalog

## Out Of Scope

- Mail, calendar, send, spend, or delete.
- Copying this tree onto the mini.
- Rewriting people, preferences, or decisions.
- Showing a different thread layout.

## Do NOT Change

- New chat and the streamed conversation path.
- The prompt for `lab-operations` and other non-personal runs.
- Vault, files, and web tool rules.

## Acceptance Criteria

1. Earlier user and assistant lines are included. The current question is not copied into that block.
2. A conversation whose only line is the current question adds no earlier block.
3. Only the latest eight lines are kept.
4. A personal follow-up prompt contains the earlier answer and the current question.
5. A lab-operations run with a stored chat line does not receive that line.
6. `python3 -m unittest tests.test_personal_turns tests.test_agent_loop tests.test_agent_worker -v` passes.

## Validation Plan

- Automated: the unittest command above.
- Manual: not run on the mini.
- Evidence to include: unittest result in Closeout.

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none
- **May run on Air?** Yes for unit tests. Lab compose on Air is forbidden.

## Execution

- **Branch:** working tree
- **Risk tier:** P2
- **Pre-PR / pre-merge gate:** `python3 -m unittest tests.test_personal_turns tests.test_agent_loop tests.test_agent_worker -v`
- **Depends on:** IWO-099
- **Human verification required:** Yes before treating a live follow-up as done
- **Reviewer / approver:** operator
- **Project status record:** `docs/features/index.md` and this file
- **Other status surfaces:** FEAT-010, `agents/catalog.md`

## Closeout

- Verification evidence: `python3 -m unittest tests.test_personal_turns tests.test_agent_loop tests.test_agent_worker tests.test_personal_reach -v` — 29 tests, OK (2026-10-08).
- Follow-ons filed: mail or calendar after the operator connects an account.
- Residual risks: eight short lines are not the whole chat. A fact that fell off still has to be in the vault or the notes folder.
- Docs/status updated: yes
- Status surfaces reconciled: index, FEAT-010, agent catalog
- Summary metadata reviewed: yes
- Planning-only change? No
- Host deploy performed? No
