# IWO-070 — Antares review handoff

**Status:** Complete  
**Priority:** P2  
**Effort:** S  
**Owner:** human  
**Feature:** FEAT-015  
**Services / Areas:** platform, docs

## Problem

A finished Antares review lists files and weakness classes, with no line and no excerpt. Those leads need a Work Order Protocol path: a summary, then draft orders a person can accept. Nothing in the scanned repository should change from the review itself.

## Decision Context

- Chosen approach: Group leads by weakness family, reject paths that are not files in the snapshot, and emit Draft Work Orders. Verdict stays uncertain when the file exists and Antares recorded no evidence.
- Alternatives rejected: Sending every lead to an implementation agent; treating an Antares title as a confirmed defect.
- Assumptions: The product repository keeps its own accepted orders. This lab only drafts them.
- Open decisions: None for this slice. Confirming each lead is a later review, file by file.

## What To Build / Fix

- `antares_handoff.build_handoff` returns a summary, rejected rows, and draft Markdown orders.
- `POST /v1/antares/runs/{id}/handoff` reads a completed run and asks the Studio which cited paths are files.
- The Antares page shows a Draft work orders action on the open run.
- The Studio job server answers `POST /v1/runs/{id}/presence` with booleans only.

## Expected Change Surface

- Expected: handoff module, Antares client, control route, job server, Security page, tests, this IWO.
- Tests: missing files rejected, traversal rejected, drafts stay Draft, no implementation flag.
- Docs/status: FEAT-015 and the feature index.

## Out Of Scope

- Editing `dentroio/agentic-factory`.
- Accepting or implementing a draft.
- Exploit write-ups.

## Do NOT Change

- Antares stays read-only. Push, merge, and deploy still require a person.
- No file contents in the presence response.
- No secrets in Git.

## Acceptance Criteria

1. A completed run can be turned into one or more Draft orders grouped by risk.
2. A path outside the snapshot, or a missing file, is rejected and left out of the orders.
3. `confirmed` is 0 and `implement` is false for this slice.
4. Unit tests cover the handoff and the presence check.

## Validation Plan

- Automated: `PYTHONPATH=platform/src python3 -m unittest tests.test_antares_handoff tests.test_antares_ui -v`
- Manual: Open the finished review and use Draft work orders.
- Evidence to include: test names and the live summary counts.

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none
- **May run on Air?** Yes — docs and unit tests only. No lab compose.

## Execution

- **Branch:** current working tree
- **Risk tier:** P2
- **Depends on:** IWO-049, FEAT-015
- **Human verification required:** Yes — accept any product Work Order before a code change
- **Project status record:** `docs/features/index.md`

## Closeout

- Verification evidence: `tests.test_antares_handoff` and `tests.test_antares_ui` passed. Live review `c3203fc3c8ce`: 84 uncertain, 0 rejected, 0 confirmed, 6 Draft orders.
- Follow-ons filed: confirm each lead before implementation
- Residual risks: drafts are groupings, not proof. A job-server restart reloads a finished report from disk.
- Docs/status updated: FEAT-015, feature index, runbook
- Status surfaces reconciled: this file
- Summary metadata reviewed: yes
- Planning-only change? No
- Host deploy performed? Yes — control-plane files and the Studio job server were updated so the button works. No product repository was edited.
