# IWO-096 — File the day's personal chats

**Status:** Complete (unit; not deployed)
**Priority:** P2
**Effort:** S
**Owner:** human (operator)
**Feature:** [FEAT-010](../features/FEAT-010-mini-personal-agent-loop.md)
**Services / Areas:** platform (scheduler, personal memory)
**Risk tier:** P2

## Problem

The personal vault can append a daily note, and nothing calls that function.
A personal-agent chat disappears from the next day's brief unless a person
copies it into `timeline/daily/`.

## Decision Context

- Chosen approach: `POST /v1/scheduler/tick` files personal-agent user and
  assistant messages for finished UTC days, once per day, into
  `timeline/daily/YYYY-MM-DD.md`. The lookback is seven days. Today's chats
  wait until that UTC date is over. A second tick does not append the same
  lines. Other agents are skipped. Preference files are not opened for write.
- Alternatives rejected: asking the answering model to call `memory_write`
  or to rewrite entity files.
- Assumptions: message `created_at` is UTC. The LaunchAgent already posts
  the tick. This IWO does not restart that agent.
- Open decisions: none in this slice.

## What To Build / Fix

- `memory_file.py` selects `personal` chats and calls `record_day`.
- `agent_scheduler.tick` accepts `file_memory` and remembers filed days in
  the existing schedule state file.
- The control-plane tick endpoint passes the conversation store and the vault.

## Expected Change Surface

- Expected: `memory_file.py`, `agent_scheduler.py`, `control_app.py`
- Tests: `tests/test_agent_scheduler.py`
- Docs/status: this file, `docs/features/index.md`, FEAT-010, `agents/personal/`

## Out Of Scope

- Rewriting people, preferences, or decisions.
- Filing ordinary Studio chats (`lab-operations` and any other agent).
- Restarting the mini control plane or the scheduler LaunchAgent.
- Adding mail, calendar, or web tools.

## Do NOT Change

- The answering model stays read-only on the vault.
- Chat completions at `/` do not gain the `TOOL` / `FINAL` dialect.
- No secrets in Git. Notes land under `~/.ai-lab/memory`.

## Acceptance Criteria

1. A personal user line and assistant line from a finished UTC day appear in
   that day's note.
2. A lab-operations message from the same day does not.
3. A message timestamped on the UTC day still in progress does not.
4. A second tick does not duplicate the line.
5. A preference file is byte-for-byte unchanged.
6. `python3 -m unittest tests.test_agent_scheduler tests.test_memory_vault -v` passes.

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
- **Pre-PR / pre-merge gate:** `python3 -m unittest tests.test_agent_scheduler tests.test_memory_vault -v`
- **Depends on:** IWO-030, IWO-095
- **Human verification required:** Yes before treating a live filed day as done
- **Reviewer / approver:** operator
- **Project status record:** `docs/features/index.md` and this file
- **Other status surfaces:** FEAT-010, `agents/catalog.md`

## Closeout

- Verification evidence: `python3 -m unittest tests.test_agent_scheduler tests.test_memory_vault -v` — 18 tests, OK (2026-10-06).
- Follow-ons filed: none. The next tool is mail or calendar, after an account is connected. Web lookup is [IWO-097](IWO-097-personal-web-lookup.md).
- Residual risks: days older than seven are not recovered. A day with more than forty lines keeps the first forty. Filing uses UTC, so an evening in US Eastern can land on the next UTC date.
- Docs/status updated: yes
- Status surfaces reconciled: index, FEAT-010, agent catalog
- Summary metadata reviewed: yes
- Planning-only change? No
- Host deploy performed? No
