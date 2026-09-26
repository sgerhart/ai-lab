# IWO-078 — Hypervisor test harness and benign end-to-end validation

**Status:** Draft  
**Priority:** P0  
**Effort:** L  
**Owner:** implementation agent  
**Feature:** FEAT-020  
**Services / Areas:** tests, platform/security, docs, scripts

## Problem

Before hostile artifacts are ever permitted, the security-compute path needs an end-to-end validation suite using harmless fixtures.

## Decision Context

- Chosen approach: Use fake provider in CI and an explicitly authorized benign live validation against either ESXi or Proxmox later.
- Alternatives rejected: duplicate security stacks; implicit host mutation; unrestricted hypervisor credentials
- Assumptions: ADR 0043 is accepted before implementation.
- Open decisions: provider-specific details must come from operator-supplied ESXi/Proxmox inventory; do not invent endpoints, credentials, VLANs, bridges, port groups, or datastores.

## What To Build / Fix

Build provider contract test suite, benign guest test fixture, expected process/network/file evidence, cleanup assertions, and operator validation report. Include a dry-run/preflight mode that never creates a VM.

## Expected Change Surface

- Expected: tests, platform/security, docs, scripts
- Tests: add deterministic unit/contract tests; no live hypervisor mutation in normal CI.
- Docs/status: update feature/index status and this IWO closeout.

## Out Of Scope

Malware samples, exploit payloads, uncontrolled Internet access, or automatic live deployment.

## Do NOT Change

No test may require a real hypervisor by default. Live test must be separately authorized and point only to operator-approved resources.

- No secrets in Git.
- No `0.0.0.0` committed binds.
- No host, hypervisor, network, model, or VM mutation without explicit authorization.
- Do not weaken existing approval gates.

## Acceptance Criteria

1. CI runs entirely with fake provider. 2. Dry-run prints intended resource operations. 3. Benign live mode can validate clone→boot→fixture→evidence→cleanup when separately authorized. 4. Residual resources fail the run. 5. Host/network safety checks are included.

## Validation Plan

- Automated: full fake-provider E2E.
- Manual/live: separate operator authorization required.
- Evidence: generated validation report.

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No by implementation alone; runtime use only after deployment authorization.
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** live hypervisor lifecycle only under separate authorization
- **May run on Air?** No

## Execution

- **Branch:** `iwo/078-hypervisor-test-harness-and-benign-end-to-end`
- **Risk tier:** P0
- **Pre-PR / pre-merge gate:** `./scripts/validate-repo.sh` plus targeted tests
- **Depends on:** IWO-077
- **Human verification required:** Yes
- **Reviewer / approver:** human operator
- **Project status record:** `docs/features/index.md`
- **Other status surfaces:** `FEAT-020`, `docs/work-orders/README.md`

## Closeout

- Verification evidence:
- Follow-ons filed:
- Residual risks:
- Docs/status updated:
- Status surfaces reconciled:
- Summary metadata reviewed:
- Planning-only change? No
- Host deploy performed? No unless separately authorized and recorded
