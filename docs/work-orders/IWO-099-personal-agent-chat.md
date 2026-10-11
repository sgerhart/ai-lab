# IWO-099 — Personal agent chat

**Status:** Complete (unit; not deployed)
**Priority:** P2
**Effort:** S
**Owner:** human (operator)
**Feature:** [FEAT-010](../features/FEAT-010-mini-personal-agent-loop.md)
**Services / Areas:** platform (studio page, agent worker)
**Risk tier:** P2

## Problem

The personal agent can read memory, notes, and the web, but every new studio
chat is `lab-operations`. Send on that chat is a model conversation. The
operator cannot start the personal agent from the sidebar.

## Decision Context

- Chosen approach: a **Personal agent** button creates a conversation with
  agent `personal`. Send on that conversation stores the user line and queues
  the existing agent run. A finished answer is also stored as an assistant
  message so the daily filer can see it. The thread shows the run card and
  hides that duplicate filing line. **New chat** stays `lab-operations`, and
  Send there still streams a conversation.
- Alternatives rejected: turning every Send into the tool loop. Putting mail
  on this slice. Mail still needs a connected account.
- Assumptions: the mini worker already drains queued runs. This page is not
  on the mini until the working tree is copied there.
- Open decisions: none in this slice.

## What To Build / Fix

- Sidebar entry and composer copy for a personal conversation.
- Refuse a chat completion or stream on a personal conversation.
- Record one assistant message when a personal run completes.

## Expected Change Surface

- Expected: `agents.html`, `control_app.py`, `agent_worker.py`
- Tests: `tests/test_personal_reach.py`, `tests/test_agent_worker.py`
- Docs/status: this file, `docs/features/index.md`, FEAT-010, agent catalog

## Out Of Scope

- Mail, calendar, send, spend, or delete.
- Attachments on a personal run.
- Copying this page onto the mini.
- Rewriting people, preferences, or decisions.

## Do NOT Change

- New chat and the streamed conversation path.
- Vault, files, and web tool rules.
- Daily filing rules. Today's chats still wait until that UTC day is over.

## Acceptance Criteria

1. The page has a Personal agent control, and a new personal conversation uses agent `personal`. New chat still uses `lab-operations`.
2. A personal conversation refuses `reply: true` and the stream endpoint. A user line with `reply: false` is stored.
3. An ordinary conversation still accepts a user line.
4. A completed personal run stores one assistant message. A second drain does not add another. A lab-operations run does not store one.
5. `python3 -m unittest tests.test_personal_reach tests.test_agent_worker -v` passes.

## Validation Plan

- Automated: the unittest command above.
- Manual: not run in the browser. This session has no browser tool, and the mini is still serving the previous page.
- Evidence to include: unittest result in Closeout.

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none
- **May run on Air?** Yes for unit tests. Lab compose on Air is forbidden.

## Execution

- **Branch:** working tree
- **Risk tier:** P2
- **Pre-PR / pre-merge gate:** `python3 -m unittest tests.test_personal_reach tests.test_agent_worker -v`
- **Depends on:** IWO-095
- **Human verification required:** Yes before treating a live personal chat as done
- **Reviewer / approver:** operator
- **Project status record:** `docs/features/index.md` and this file
- **Other status surfaces:** FEAT-010, `agents/catalog.md`

## Closeout

- Verification evidence: `python3 -m unittest tests.test_personal_reach tests.test_agent_worker -v` — 7 tests, OK (2026-10-07). No browser in this session, so the sidebar was not clicked.
- Follow-ons filed: mail or calendar after the operator connects an account. Copy this page to the mini only when asked.
- Residual risks: the answer the operator sees is the run card. The filed assistant line is hidden in the thread so it is not shown twice.
- Docs/status updated: yes
- Status surfaces reconciled: index, FEAT-010, agent catalog
- Summary metadata reviewed: yes
- Planning-only change? No
- Host deploy performed? No
