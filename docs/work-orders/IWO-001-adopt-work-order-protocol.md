# IWO-001 — Adopt Work Order Protocol as AI Lab specification standard

**Status:** Complete  
**Priority:** P1  
**Effort:** S  
**Owner:** operator  
**Feature:** [FEAT-001](../features/FEAT-001-work-order-planning-and-approval.md)  
**Services / Areas:** docs, templates, agent process  
**Risk tier:** P3 (documentation / process only; no host change)  
**GitHub:** ties to [#2](https://github.com/sgerhart/ai-lab/issues/2)

## Problem

`docs/features/` established a backlog, but AI Lab had not adopted
[`dentroio/work-order-protocol`](https://github.com/dentroio/work-order-protocol)
as the **implementation work-order** specification standard. Evidence on `main`:

- `.github/ISSUE_TEMPLATE/work_order.md` was a short stub (Problem / In scope /
  Out of scope / Acceptance / Deploy?).
- No root `AGENT_PROCESS.md`.
- No canonical `templates/WO-template.md`.
- Historical `WO-000`–`WO-007` remain phase records and must not be confused
  with protocol Work Orders or with Postgres runtime jobs.

Without that adoption, planning agents and humans lack a shared cold-start
contract, and the protocol lifecycle is not mapped to AI Lab runtime states.

## Decision Context

- **Chosen approach:** Adopt protocol Level 1–2 for *implementation* work
  orders in Git; keep AI Lab Features (`FEAT-*`) and runtime jobs (Postgres
  UUIDs) as separate entities; document stricter host-deploy gates.
- **Alternatives rejected:** Replace runtime schema with protocol statuses
  (rejected — harness already uses ADR 0020 states). Vendor the entire
  protocol book into this repo (rejected — reference upstream; adapt only
  what AI Lab needs).
- **Assumptions:** Upstream protocol remains readable at
  `$HOME/workspace/github/dentroio/work-order-protocol` and on GitHub.
- **Open decisions:** None for this IWO. Factory Level 4 automation is out of
  scope.

## What To Build / Fix

- Root `AGENT_PROCESS.md` adapted for AI Lab (no deploy without human auth).
- Canonical `templates/WO-template.md` (protocol shape + AI Lab deploy /
  runtime fields).
- Expand GitHub issue template to match the canonical template.
- `docs/work-order-protocol/` with adoption README, lifecycle mapping to
  runtime `Status`, and risk/deploy gates.
- ADR 0036 recording the adoption.
- Navigation + `validate-repo.sh` checks.
- Mark this IWO complete with verification evidence.

## Expected Change Surface

- Expected: docs, templates, `AGENT_PROCESS.md`, ADR, validate-repo, README links
- Tests: validate-repo / structure / safety scripts (no platform behavior change)
- Docs/status: features index, work-orders README, roadmap note

## Out Of Scope

- Studio bring-up or model pulls.
- Implementing a planning agent.
- Changing Postgres runtime schema or LangGraph nodes.
- Enabling Agentic Factory / Level 4 automation in this repo.
- Renaming historical `WO-000`–`WO-007`.

## Do NOT Change

- Bind policy (no `0.0.0.0`).
- Requirement for explicit human authorization before host mutate / deploy /
  pull / restore.
- Separation of Clarion / factory stacks (ADR 0007, 0025).
- Runtime status enum values in `work_order.py` (map only; do not rename).

## Acceptance Criteria

1. `AGENT_PROCESS.md` and `templates/WO-template.md` exist on the repo root /
   templates path.
2. GitHub work-order issue template is no longer the short stub; it includes
   Problem, What To Build, Out Of Scope, Do NOT Change, Acceptance, Validation,
   Execution, and AI Lab deploy/runtime gates.
3. Docs map protocol lifecycle states to runtime `created`…`cancelled` and
   state that accepting an IWO does **not** authorize deploy.
4. ADR 0036 accepted and listed in `docs/decisions/README.md`.
5. `./scripts/validate-repo.sh` and `./tests/test_scripts_safety.sh` pass.
6. No host scripts run with `--apply`, no compose `up`, no runtime job created
   by this IWO.

## Validation Plan

- Automated: `./scripts/validate-repo.sh`, `./tests/test_scripts_safety.sh`,
  `python3 -m unittest discover -s tests -v` (or platform venv equivalent).
- Manual: cold-read `AGENT_PROCESS.md` + lifecycle mapping; confirm issue
  template fields.
- Evidence: command exit codes in Closeout.

## Execution

- **Branch:** `main` (docs-only; operator-authorized commit separately)
- **Risk tier:** P3
- **Pre-PR / pre-merge gate:** `./scripts/validate-repo.sh`
- **Depends on:** FEAT-001 docs tree (`a189898`)
- **Human verification required:** Yes (process adoption)
- **Reviewer / approver:** operator
- **Project status record:** `docs/features/index.md` + this file
- **Other status surfaces:** GitHub issue #2

## Closeout

- Verification evidence:
  - `./scripts/validate-repo.sh` → RESULT: OK
  - `./tests/test_scripts_safety.sh` → script safety OK
  - `./tests/test_structure.sh` → OK (via validate-repo)
  - `python3 -m unittest discover -s tests -v` → exit 0
- Follow-ons filed: Studio bring-up (host); FEAT-003; planning-agent IWOs
  (IWO-001-b+) still future
- Residual risks: contributors may still paste short issues until the expanded
  template is habit
- Docs/status updated: Yes (`docs/features/index.md`, roadmap, FEAT-001)
- Status surfaces reconciled: Yes
- Summary metadata reviewed: Yes
- Planning-only change? No — this IWO *implements* the docs adoption (still
  no host mutate)
- Host deploy performed? No

