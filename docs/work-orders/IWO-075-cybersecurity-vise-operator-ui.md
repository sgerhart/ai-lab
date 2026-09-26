# IWO-075 — Cybersecurity Vise operator UI

**Status:** Draft  
**Priority:** P2  
**Effort:** L  
**Owner:** implementation agent  
**Feature:** FEAT-019  
**Services / Areas:** platform web, platform/security, docs, tests

## Problem

Operators need to submit and review Vise jobs without using raw hypervisor consoles for ordinary workflow.

## Decision Context

- Chosen approach: Add Vise to the existing Security Center.
- Alternatives rejected: duplicate security stacks; implicit host mutation; unrestricted hypervisor credentials
- Assumptions: ADR 0043 is accepted before implementation.
- Open decisions: provider-specific details must come from operator-supplied ESXi/Proxmox inventory; do not invent endpoints, credentials, VLANs, bridges, port groups, or datastores.

## What To Build / Fix

Build artifact metadata intake, profile/provider/template selection from approved inventories, preflight status, approval state, lifecycle timeline, evidence summary, findings, cleanup verification, and residual-risk display.

## Expected Change Surface

- Expected: platform web, platform/security, docs, tests
- Tests: add deterministic unit/contract tests; no live hypervisor mutation in normal CI.
- Docs/status: update feature/index status and this IWO closeout.

## Out Of Scope

Uploading large binaries before an artifact storage decision is implemented; direct console control.

## Do NOT Change

UI must not provide a generic hypervisor shell or one-click bypass of isolation/approval.

- No secrets in Git.
- No `0.0.0.0` committed binds.
- No host, hypervisor, network, model, or VM mutation without explicit authorization.
- Do not weaken existing approval gates.

## Acceptance Criteria

1. UI exposes preflight and cleanup proof. 2. Start-execution action is disabled until approval/isolation are satisfied. 3. Evidence is viewable without direct guest trust. 4. Provider errors are explicit.

## Validation Plan

- Automated: UI/API tests.
- Manual: fake-provider benign workflow.
- Evidence: screenshots optional.

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No by implementation alone; runtime use only after deployment authorization.
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** approval action
- **May run on Air?** Yes — browser client only

## Execution

- **Branch:** `iwo/075-cybersecurity-vise-operator-ui`
- **Risk tier:** P2
- **Pre-PR / pre-merge gate:** `./scripts/validate-repo.sh` plus targeted tests
- **Depends on:** IWO-069,IWO-070,IWO-074
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
