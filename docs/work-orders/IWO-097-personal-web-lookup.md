# IWO-097 — Personal agent web lookup

**Status:** Complete (unit; not deployed)
**Priority:** P2
**Effort:** S
**Owner:** human (operator)
**Feature:** [FEAT-010](../features/FEAT-010-mini-personal-agent-loop.md)
**Services / Areas:** platform (personal agent, web lookup)
**Risk tier:** P2

## Problem

The personal agent can read its vault and cannot look up a fact outside it.
Chat already searches the public web. The agent loop did not.

## Decision Context

- Chosen approach: `web_search` takes a factual question. The lab searches
  Wikipedia and DuckDuckGo and fetches one public HTTPS page, using the same
  checks as chat. The model does not supply the URL. A URL in the question or
  in the tool arguments is not fetched. The tool may run again with a new
  question. It is on the `personal` policy only.
- Alternatives rejected: mail or calendar first, because those need an account
  the operator has not connected. A general file read of the home directory.
- Assumptions: public page fetches stay on the existing source-fetch checks.
- Open decisions: none in this slice.

## What To Build / Fix

- `web_lookup.py` and a `web_search` handler.
- `agents/personal/policy.json` allows it. Lab agents do not.

## Expected Change Surface

- Expected: `web_lookup.py`, `tool_runtime.py`, `tools.py`, `agent_loop.py`,
  `tool_catalog.py`, `capabilities.py`, `agents/personal/policy.json`
- Tests: `tests/test_web_lookup.py`
- Docs/status: this file, `docs/features/index.md`, FEAT-010, agent catalog

## Out Of Scope

- Gmail, calendar, payments, or sending.
- Letting the model choose a URL.
- Restarting the mini control plane.
- Filing web pages into the memory vault.

## Do NOT Change

- Ordinary chat grounding.
- The answering model stays unable to write the vault.
- No secrets in Git.

## Acceptance Criteria

1. A factual question returns the page the lab selected and an excerpt from it.
2. A URL in the question is not fetched.
3. A URL passed as a tool argument is not fetched.
4. A personal run can call `web_search` twice with different questions.
5. `python3 -m unittest tests.test_web_lookup -v` passes.

## Validation Plan

- Automated: `python3 -m unittest tests.test_web_lookup tests.test_tool_catalog -v`
- Manual: not run on the mini. Tests use a fake HTTP opener.
- Evidence to include: unittest result in Closeout.

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none
- **May run on Air?** Yes for unit tests. Lab compose on Air is forbidden.

## Execution

- **Branch:** working tree
- **Risk tier:** P2
- **Pre-PR / pre-merge gate:** `python3 -m unittest tests.test_web_lookup -v`
- **Depends on:** IWO-095, IWO-082
- **Human verification required:** Yes before treating a live lookup as done
- **Reviewer / approver:** operator
- **Project status record:** `docs/features/index.md` and this file
- **Other status surfaces:** FEAT-010, `agents/catalog.md`

## Closeout

- Verification evidence: `python3 -m unittest tests.test_web_lookup tests.test_tool_catalog tests.test_memory_vault.PersonalAgentLoopTests -v` — 11 tests, OK (2026-10-06).
- Follow-ons filed: notes folder is [IWO-098](IWO-098-personal-files-folder.md). Mail or calendar still waits on a connected account.
- Residual risks: the page is untrusted text in the tool observation. The loop still asks the model to treat tool text as data in the system prompt for chat, and the agent prompt says not to invent tool results.
- Docs/status updated: yes
- Status surfaces reconciled: index, FEAT-010, agent catalog
- Summary metadata reviewed: yes
- Planning-only change? No
- Host deploy performed? No
