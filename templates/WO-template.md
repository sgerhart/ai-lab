# WO-NNN / IWO-NNN — Short Descriptive Title

**Status:** Draft | Ready | Accepted | In Progress | Review | Complete | Blocked  
**Priority:** P0 | P1 | P2 | P3  
**Effort:** XS | S | M | L | XL  
**Owner:** human or team  
**Feature:** FEAT-NNN | none  
**Services / Areas:** platform, docs, hosts, infrastructure, agents, models, none

Canonical AI Lab implementation Work Order template. Adapted from
[`dentroio/work-order-protocol`](https://github.com/dentroio/work-order-protocol)
`templates/WO-template.md` (ADR 0036).

For GitHub issues, use the Work order issue form (same sections).

## Problem

Describe the visible problem, missing capability, or reason this work exists.
Include evidence: routes, file paths, logs, failing test, or observed behavior.

Do not hide the solution in this section.

## Decision Context

- Chosen approach:
- Alternatives rejected:
- Assumptions:
- Open decisions:

Omit or keep short if the work is straightforward.

## What To Build / Fix

Describe the concrete implementation:

- files or areas likely touched
- API contracts
- data model changes
- UI behavior
- docs required

## Expected Change Surface

- Expected:
- Tests:
- Docs/status:

## Out Of Scope

- Tempting adjacent work that should not be included.
- Follow-on ideas that deserve separate Work Orders.

## Do NOT Change

- Hard invariants.
- Existing behavior that must be preserved.
- Areas intentionally excluded.
- AI Lab defaults: no secrets in Git; no `0.0.0.0` binds; no host mutate without
  explicit human authorization.

## Acceptance Criteria

1. Concrete, checkable outcome.
2. Command, URL, visible result, or artifact.
3. Quality gate passes (`./scripts/validate-repo.sh` unless this IWO says otherwise).

## Validation Plan

- Automated:
- Manual:
- Evidence to include:

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** Yes / No (default **No**)
- **Host deploy / mutate authorized by this IWO alone?** **No** — always requires
  a separate human authorization (`brew`/`compose`/`colima`/`ollama pull`/
  restore/SSH/firewall/Tailscale ACL).
- **Privileged tools expected?** list or none (ADR 0018)
- **May run on Air?** Yes / No — lab compose on Air is forbidden (ADR 0025)

## Execution

- **Branch:** `iwo/NNN-short-name` or `wo/NNN-short-name`
- **Risk tier:** P0 | P1 | P2 | P3
- **Pre-PR / pre-merge gate:** command or checklist
- **Depends on:** none | IWO-NNN | FEAT-NNN | historical WO-NNN
- **Human verification required:** Yes / No
- **Reviewer / approver:** person or role
- **Project status record:** `docs/features/index.md` | this file | GitHub issue
- **Other status surfaces:** capability issue, none

## Closeout

- Verification evidence:
- Follow-ons filed:
- Residual risks:
- Docs/status updated:
- Status surfaces reconciled:
- Summary metadata reviewed:
- Planning-only change? Yes / No
- Host deploy performed? Yes / No (must be No unless separately authorized and recorded)
