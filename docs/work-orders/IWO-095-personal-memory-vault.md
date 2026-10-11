# IWO-095 — Personal memory vault and brief

**Status:** Complete (unit; not deployed)
**Priority:** P2
**Effort:** M
**Owner:** human (operator)
**Feature:** [FEAT-010](../features/FEAT-010-mini-personal-agent-loop.md)
**Services / Areas:** platform (agent loop, personal agent)
**Risk tier:** P2

## Problem

The personal-agent loop sends one objective plus the last few tool notes. It
does not know who the operator is, what work is open, or how to look a fact
up in words. Repeating a tool name ends the run, so a search cannot be
followed by a read and a second search.

Ordinary Studio chat is a conversation with a model and must stay that way.

## Decision Context

- Chosen approach: a markdown vault at `~/.ai-lab/memory` (override
  `AI_LAB_MEMORY_VAULT` in tests). The `personal` agent receives a dated brief
  and may call `vault_list`, `vault_grep`, and `vault_read` again when the
  arguments change. `record_day` appends `timeline/daily/YYYY-MM-DD.md` and
  does not edit people, preferences, or decisions. The answering model has no
  write tool.
- Alternatives rejected: storing this memory as another Qdrant collection.
  Fetched research pages stay on that path.
- Assumptions: one operator vault on the mini. The identity file is filled by
  the operator. This slice does not invent a name or a timezone.
- Open decisions: when the scheduler should call `record_day`. Not in this
  slice.

## What To Build / Fix

- `memory_vault.py` layout, brief, list, grep, read, and `record_day`.
- `agents/personal/policy.json` with the three read tools.
- Brief injected only when `step_agent_run` is the `personal` agent.
- Lab agents still stop when the same tool name is repeated.

## Expected Change Surface

- Expected: `memory_vault.py`, `agent_loop.py`, `tool_runtime.py`, `tools.py`,
  `tool_catalog.py`, `capabilities.py`, `agents/personal/`.
- Tests: `tests/test_memory_vault.py`
- Docs/status: this file, `docs/features/index.md`, FEAT-010, agent catalog.

## Out Of Scope

- Changing Studio chat at `/`.
- A model that rewrites entity files.
- Hooking `record_day` to the LaunchAgent tick.
- Mail, calendar, browser, phone, or payments.
- Deploying or restarting the mini control plane.

## Do NOT Change

- `lab-operations` still stops on a repeated tool name.
- Chat completions do not use the `TOOL` / `FINAL` brief.
- No secrets in Git. The vault is outside the repository.
- No host deploy from this IWO.

## Acceptance Criteria

1. `vault_grep` for an alias returns that file. A paraphrase with none of those
   words returns hits=0.
2. `vault_read` of a path with `..` fails and does not open a file outside the
   vault. A symlink to an outside file is not listed.
3. A `personal` run can grep, read, and grep again with a new query inside the
   step budget. A second `health_read` on `lab-operations` still stops.
4. `record_day` appends the daily note and leaves a preference file unchanged.
5. `python3 -m unittest tests.test_memory_vault tests.test_agent_loop -v` passes.

## Validation Plan

- Automated: the unittest command above.
- Manual: not run on the mini. The control plane was not restarted.
- Evidence to include: unittest result in Closeout.

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none
- **May run on Air?** Yes for unit tests. Lab compose on Air is forbidden.

## Execution

- **Branch:** working tree
- **Risk tier:** P2
- **Pre-PR / pre-merge gate:** `python3 -m unittest tests.test_memory_vault tests.test_agent_loop -v`
- **Depends on:** IWO-005, IWO-020, FEAT-010
- **Human verification required:** Yes before treating a live personal run as done
- **Reviewer / approver:** operator
- **Project status record:** `docs/features/index.md` and this file
- **Other status surfaces:** FEAT-010, `agents/catalog.md`

## Closeout

- Verification evidence: `python3 -m unittest tests.test_memory_vault tests.test_agent_loop tests.test_tool_catalog tests.test_capabilities -v` — 32 tests, OK (2026-10-05).
- Follow-ons filed: scheduler filing is [IWO-096](IWO-096-file-personal-day.md).
- Residual risks: the brief is only as fresh as `identity.md`, open work files, and the daily note. The answering model can still finish early if it emits `FINAL` before searching.
- Docs/status updated: yes
- Status surfaces reconciled: index, FEAT-010, agent catalog
- Summary metadata reviewed: yes
- Planning-only change? No
- Host deploy performed? No
