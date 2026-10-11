# IWO-098 — Personal notes folder

**Status:** Complete (unit; not deployed)
**Priority:** P2
**Effort:** S
**Owner:** human (operator)
**Feature:** [FEAT-010](../features/FEAT-010-mini-personal-agent-loop.md)
**Services / Areas:** platform (personal agent, files)
**Risk tier:** P2

## Problem

The personal agent can read its memory vault and look up the web. It cannot
open a note the operator dropped in a folder. The vault is memory the filer
writes. Working notes are a different folder.

## Decision Context

- Chosen approach: `~/.ai-lab/files` (override `AI_LAB_FILES_ROOT` in tests).
  `files_list`, `files_grep`, and `files_read` see `.md` and `.txt` only.
  Paths stay inside that folder. Symlinks are skipped. The answering model
  cannot write the folder. Mail and calendar stay out until an account exists.
- Alternatives rejected: reading the home directory. Reusing the memory vault
  as a scratch pad.
- Assumptions: the operator puts notes in that folder. The lab does not create
  sample notes.
- Open decisions: none in this slice.

## What To Build / Fix

- `operator_files.py` and three read tools on the `personal` policy.
- The same tool may run again with new arguments, inside the step budget.

## Expected Change Surface

- Expected: `operator_files.py`, `tool_runtime.py`, `tools.py`, `agent_loop.py`,
  `tool_catalog.py`, `capabilities.py`, `agents/personal/policy.json`
- Tests: `tests/test_operator_files.py`
- Docs/status: this file, `docs/features/index.md`, FEAT-010, agent catalog

## Out Of Scope

- Writing, deleting, or moving notes.
- Reading the memory vault through these tools.
- Mail, calendar, send, spend, or delete.
- Restarting the mini control plane.

## Do NOT Change

- Vault reads and daily filing.
- Web lookup URL rules.
- Ordinary chat.

## Acceptance Criteria

1. A word in a note is found. A phrase that is not in the note returns hits=0.
2. A path with `..` fails and does not open a file outside the folder.
3. A symlink to an outside file is not listed.
4. A search of the files folder does not return text that exists only in another directory.
5. A personal run can grep and then read.
6. `python3 -m unittest tests.test_operator_files -v` passes.

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
- **Pre-PR / pre-merge gate:** `python3 -m unittest tests.test_operator_files -v`
- **Depends on:** IWO-095
- **Human verification required:** Yes before treating a live notes read as done
- **Reviewer / approver:** operator
- **Project status record:** `docs/features/index.md` and this file
- **Other status surfaces:** FEAT-010, `agents/catalog.md`

## Closeout

- Verification evidence: `python3 -m unittest tests.test_operator_files -v` — 6 tests, OK (2026-10-06).
- Follow-ons filed: mail or calendar after the operator connects an account.
- Residual risks: notes are untrusted text in the tool observation, same as a web page. The folder is created only when code calls `ensure_folder`; the read tools do not create it.
- Docs/status updated: yes
- Status surfaces reconciled: index, FEAT-010, agent catalog
- Summary metadata reviewed: yes
- Planning-only change? No
- Host deploy performed? No
