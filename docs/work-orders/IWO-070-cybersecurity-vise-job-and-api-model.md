# IWO-070 — Cybersecurity Vise job and API model

**Status:** Complete (unit; not deployed)  
**Priority:** P1  
**Effort:** L  
**Owner:** implementation agent  
**Feature:** FEAT-019  
**Services / Areas:** platform/security, platform/api, docs, tests

## Problem

AI Lab needs a durable, auditable job model for hostile-artifact analysis distinct from ordinary work orders and from Antares code review.

## Decision Context

- Chosen approach: Define Vise jobs as security-analysis records correlated to runtime orchestration but with explicit analysis/isolation state.
- Alternatives rejected: duplicate security stacks; implicit host mutation; unrestricted hypervisor credentials
- Assumptions: ADR 0043 is accepted before implementation.
- Open decisions: provider-specific details must come from operator-supplied ESXi/Proxmox inventory; do not invent endpoints, credentials, VLANs, bridges, port groups, or datastores.

## What To Build / Fix

Implement Vise job schema/API for artifact metadata, profile, requested hypervisor provider, template, isolation preflight, approvals, lifecycle state, evidence refs, cleanup status, and findings. Store hashes/metadata; do not store executable bytes in Git.

## Expected Change Surface

- Expected: platform/security, platform/api, docs, tests
- Tests: add deterministic unit/contract tests; no live hypervisor mutation in normal CI.
- Docs/status: update feature/index status and this IWO closeout.

## Out Of Scope

Hypervisor execution or sample storage backend.

## Do NOT Change

Do not overload Antares jobs or ordinary coding runs with malware-specific lifecycle.

- No secrets in Git.
- No `0.0.0.0` committed binds.
- No host, hypervisor, network, model, or VM mutation without explicit authorization.
- Do not weaken existing approval gates.

## Acceptance Criteria

1. Job state machine covers submitted→preflight→ready→approval→running→collecting→cleanup→complete/failed. 2. Cleanup status is mandatory. 3. Untrusted execution cannot enter running without approval. 4. Evidence references use IWO-066 model.

## Validation Plan

- Automated: state-transition and approval tests.
- Manual: benign fixture flow using fake provider.
- Evidence: state trace.

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No by implementation alone; runtime use only after deployment authorization.
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** approval service
- **May run on Air?** No

## Execution

- **Branch:** `iwo/070-cybersecurity-vise-job-and-api-model`
- **Risk tier:** P1
- **Pre-PR / pre-merge gate:** `./scripts/validate-repo.sh` plus targeted tests
- **Depends on:** IWO-066
- **Human verification required:** Yes
- **Reviewer / approver:** human operator
- **Project status record:** `docs/features/index.md`
- **Other status surfaces:** `FEAT-019`, `docs/work-orders/README.md`

## Closeout

- Verification evidence: `python3 -m unittest tests.test_vise tests.test_security_platform`
- Follow-ons filed: IWO-071 ships the fake adapter used by preflight. IWO-072 still owns the operator network names.
- Residual risks: jobs live in process memory. Proxmox and ESXi adapters refuse every call. ADR 0043 is still Proposed.
- Docs/status updated: `docs/features/index.md`, this closeout
- Status surfaces reconciled: yes
- Summary metadata reviewed: yes
- Planning-only change? No
- Host deploy performed? No
