# IWO-101 — Personal research reports

**Status:** Complete (unit; not deployed)
**Priority:** P2
**Effort:** S
**Owner:** human (operator)
**Feature:** [FEAT-010](../features/FEAT-010-mini-personal-agent-loop.md)
**Services / Areas:** platform (personal agent, research)
**Risk tier:** P2

## Problem

The personal agent can look up one public page. It cannot gather several
sources, write a report, or revise that report when the operator asks for
more depth.

## Decision Context

- Chosen approach: `research` searches Wikipedia and DuckDuckGo and fetches up
  to five public pages. The lab chooses the URLs. The full excerpts go into
  `~/.ai-lab/reports/<name>.sources.md`, and a later call with the same name
  appends. `report_write` saves or replaces `<name>.md`. `report_read` and
  `report_list` open what was saved. The operator keeps talking in the same
  personal chat to revise or go deeper.
- Alternatives rejected: letting the model choose the URL. Writing into the
  memory vault or the notes folder. Turning New chat into this loop.
- Assumptions: five pages and a 48,000-character report are the bound for this
  slice. A local model still has to write the report from those sources.
- Open decisions: none in this slice.

## What To Build / Fix

- `research_pages` and a report folder with list, read, write, and dossier append.
- Those tools on the `personal` policy. They may run again with new arguments.

## Expected Change Surface

- Expected: `web_lookup.py`, `source_fetch.py`, `research_reports.py`, `tool_runtime.py`, `agent_loop.py`, `tool_catalog.py`, `capabilities.py`, `agents/personal/policy.json`, `agents.html`
- Tests: `tests/test_research_reports.py`
- Docs/status: this file, `docs/features/index.md`, FEAT-010, agent catalog

## Out Of Scope

- Mail, calendar, send, spend, or delete.
- Deleting a report.
- Copying this tree onto the mini.
- Fetching a URL the model or the operator typed.

## Do NOT Change

- One-page `web_search`.
- New chat.
- Vault and notes writes. Those folders stay read-only for the model.

## Acceptance Criteria

1. A research question returns two pages the lab chose, including text from each.
2. A URL in the question is not fetched.
3. A report can be written and then replaced. The old wording is gone.
4. A path with `..` and a symlink do not change a file outside the reports folder.
5. A second research pass on the same name appends to the source dossier.
6. A personal run can research, write a report, and replace it.
7. `python3 -m unittest tests.test_research_reports tests.test_web_lookup tests.test_agent_loop -v` passes.

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
- **Pre-PR / pre-merge gate:** `python3 -m unittest tests.test_research_reports tests.test_web_lookup tests.test_agent_loop -v`
- **Depends on:** IWO-099, IWO-100
- **Human verification required:** Yes before treating a live research report as done
- **Reviewer / approver:** operator
- **Project status record:** `docs/features/index.md` and this file
- **Other status surfaces:** FEAT-010, `agents/catalog.md`

## Closeout

- Verification evidence: `python3 -m unittest tests.test_research_reports tests.test_web_lookup tests.test_agent_loop tests.test_personal_reach -v` — 31 tests, OK (2026-10-09).
- Follow-ons filed: mail or calendar after the operator connects an account. Copy this tree to the mini only when asked.
- Residual risks: five pages is the cap for one call. The report is only as careful as the model that writes it. The source dossier keeps the fetched text.
- Docs/status updated: yes
- Status surfaces reconciled: index, FEAT-010, agent catalog
- Summary metadata reviewed: yes
- Planning-only change? No
- Host deploy performed? No
