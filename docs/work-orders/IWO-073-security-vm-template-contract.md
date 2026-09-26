# IWO-073 — Security VM template contract

**Status:** Draft  
**Priority:** P1  
**Effort:** L  
**Owner:** implementation agent  
**Feature:** FEAT-019  
**Services / Areas:** docs, platform/security, tests, infrastructure

## Problem

Repeatable Vise jobs need known-clean, testable Windows/Linux templates without letting the security agent mutate golden images implicitly.

## Decision Context

- Chosen approach: Define immutable template profiles and validation checks; build tooling produces instructions/automation but deployment stays gated.
- Alternatives rejected: duplicate security stacks; implicit host mutation; unrestricted hypervisor credentials
- Assumptions: ADR 0043 is accepted before implementation.
- Open decisions: provider-specific details must come from operator-supplied ESXi/Proxmox inventory; do not invent endpoints, credentials, VLANs, bridges, port groups, or datastores.

## What To Build / Fix

Add template manifest schema: OS, tools, sensors, expected snapshot, network policy, guest-agent readiness, disposable credentials policy, version, hashes where applicable. Add validation command/API. Provide Windows and Linux baseline profiles without secrets.

## Expected Change Surface

- Expected: docs, platform/security, tests, infrastructure
- Tests: add deterministic unit/contract tests; no live hypervisor mutation in normal CI.
- Docs/status: update feature/index status and this IWO closeout.

## Out Of Scope

Installing tools on live hypervisors/VMs in this IWO.

## Do NOT Change

Security agent may validate but not silently modify golden templates.

- No secrets in Git.
- No `0.0.0.0` committed binds.
- No host, hypervisor, network, model, or VM mutation without explicit authorization.
- Do not weaken existing approval gates.

## Acceptance Criteria

1. Template manifest validates offline. 2. Missing required tool/snapshot fails preflight. 3. Version drift is reported. 4. Windows/Linux profiles exist.

## Validation Plan

- Automated: manifest validation tests.
- Manual: operator maps profiles to real templates later.
- Evidence: sample validation reports.

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No by implementation alone; runtime use only after deployment authorization.
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none until live validation
- **May run on Air?** No

## Execution

- **Branch:** `iwo/073-security-vm-template-contract`
- **Risk tier:** P1
- **Pre-PR / pre-merge gate:** `./scripts/validate-repo.sh` plus targeted tests
- **Depends on:** IWO-071,IWO-072
- **Human verification required:** Yes
- **Reviewer / approver:** human operator
- **Project status record:** `docs/features/index.md`
- **Other status surfaces:** `FEAT-019`, `docs/work-orders/README.md`

## Closeout

- Verification evidence:
- Follow-ons filed:
- Residual risks:
- Docs/status updated:
- Status surfaces reconciled:
- Summary metadata reviewed:
- Planning-only change? No
- Host deploy performed? No unless separately authorized and recorded
