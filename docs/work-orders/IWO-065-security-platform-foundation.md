# IWO-065 — Security platform foundation

**Status:** Complete (unit; not deployed)  
**Priority:** P1  
**Effort:** M  
**Owner:** implementation agent  
**Feature:** FEAT-018  
**Services / Areas:** platform, docs, tests

## Problem

Security controls currently live across approvals, policy, observability, DefenseClaw summaries, and Antares without a common platform-security module.

## Decision Context

- Chosen approach: Add a common `platform/security` domain layer while preserving existing approval authority.
- Alternatives rejected: duplicate security stacks; implicit host mutation; unrestricted hypervisor credentials
- Assumptions: ADR 0043 is accepted before implementation.
- Open decisions: provider-specific details must come from operator-supplied ESXi/Proxmox inventory; do not invent endpoints, credentials, VLANs, bridges, port groups, or datastores.

## What To Build / Fix

Create security package boundaries, interfaces, provider registration, policy/evaluation contracts, and API-facing service abstractions. Do not move credentials or deploy services.

## Expected Change Surface

- Expected: platform, docs, tests
- Tests: add deterministic unit/contract tests; no live hypervisor mutation in normal CI.
- Docs/status: update feature/index status and this IWO closeout.

## Out Of Scope

Security Center UI, hypervisor integration, or host deployment.

## Do NOT Change

Do not replace `policy.py`, `approvals.py`, or observability; integrate them.

- No secrets in Git.
- No `0.0.0.0` committed binds.
- No host, hypervisor, network, model, or VM mutation without explicit authorization.
- Do not weaken existing approval gates.

## Acceptance Criteria

1. `platform/security` imports cleanly. 2. Provider interface supports Antares/DefenseClaw/Vise-style integrations. 3. Existing tests still pass. 4. Security service has no network side effects at import/startup.

## Validation Plan

- Automated: unit tests for provider registry and policy handoff.
- Manual: inspect architecture boundaries.
- Evidence: test output and file list.

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No by implementation alone; runtime use only after deployment authorization.
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none
- **May run on Air?** Yes — client/dev only

## Execution

- **Branch:** `iwo/065-security-platform-foundation`
- **Risk tier:** P1
- **Pre-PR / pre-merge gate:** `./scripts/validate-repo.sh` plus targeted tests
- **Depends on:** ADR 0043
- **Human verification required:** Yes
- **Reviewer / approver:** human operator
- **Project status record:** `docs/features/index.md`
- **Other status surfaces:** `FEAT-018`, `docs/work-orders/README.md`

## Closeout

- Verification evidence: `python3 -m unittest tests.test_security_platform tests.test_approvals tests.test_repo_finish tests.test_defenseclaw_report` — 32 tests OK (2026-09-26).
- Follow-ons filed: IWO-068 and IWO-069 stay Draft (Agent Studio posture and Security Center UI).
- Residual risks: routes are in the API process and are not live until an authorized restart. Provider rows do not call Antares, DefenseClaw, or a hypervisor.
- Docs/status updated: this file, FEAT-018, `docs/features/index.md`, `docs/work-orders/README.md`, `docs/architecture/control-plane.md`
- Status surfaces reconciled: yes
- Summary metadata reviewed: yes
- Planning-only change? No
- Host deploy performed? No
