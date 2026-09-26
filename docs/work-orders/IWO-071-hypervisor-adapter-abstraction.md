# IWO-071 — Hypervisor adapter abstraction

**Status:** Complete (unit; not deployed)  
**Priority:** P1  
**Effort:** L  
**Owner:** implementation agent  
**Feature:** FEAT-019  
**Services / Areas:** platform/security, platform/tools, docs, tests

## Problem

The security agent needs one bounded contract for ESXi and Proxmox instead of embedding vendor APIs in agent logic.

## Decision Context

- Chosen approach: Create provider-neutral hypervisor interface with separate ESXi and Proxmox adapters.
- Alternatives rejected: duplicate security stacks; implicit host mutation; unrestricted hypervisor credentials
- Assumptions: ADR 0043 is accepted before implementation.
- Open decisions: provider-specific details must come from operator-supplied ESXi/Proxmox inventory; do not invent endpoints, credentials, VLANs, bridges, port groups, or datastores.

## What To Build / Fix

Define inventory, template validation, ephemeral clone, power, snapshot/revert, NIC/network validation, guest readiness, destroy, and residual-resource checks. Implement fake adapter for CI. Provider implementations must use allowlisted resources and secret references.

## Expected Change Surface

- Expected: platform/security, platform/tools, docs, tests
- Tests: add deterministic unit/contract tests; no live hypervisor mutation in normal CI.
- Docs/status: update feature/index status and this IWO closeout.

## Out Of Scope

Real host deployment, credentials, or provider network configuration.

## Do NOT Change

Do not expose generic arbitrary API calls or arbitrary shell/SSH through this interface.

- No secrets in Git.
- No `0.0.0.0` committed binds.
- No host, hypervisor, network, model, or VM mutation without explicit authorization.
- Do not weaken existing approval gates.

## Acceptance Criteria

1. Fake adapter passes full lifecycle. 2. Provider contract can represent both ESXi and Proxmox. 3. All mutating methods require job/resource IDs and authorization context. 4. Arbitrary host operations are impossible through the public interface.

## Validation Plan

- Automated: contract suite against fake providers.
- Manual: review ESXi/Proxmox mapping docs.
- Evidence: adapter matrix.

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No by implementation alone; runtime use only after deployment authorization.
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** hypervisor API later
- **May run on Air?** No

## Execution

- **Branch:** `iwo/071-hypervisor-adapter-abstraction`
- **Risk tier:** P1
- **Pre-PR / pre-merge gate:** `./scripts/validate-repo.sh` plus targeted tests
- **Depends on:** IWO-065,IWO-070
- **Human verification required:** Yes
- **Reviewer / approver:** human operator
- **Project status record:** `docs/features/index.md`
- **Other status surfaces:** `FEAT-019`, `docs/work-orders/README.md`

## Closeout

- Verification evidence: `python3 -m unittest tests.test_vise`
- Follow-ons filed: a live Proxmox adapter waits on D-021. It is not this work order.
- Residual risks: fixture template names (`fixture-linux`, `fixture-windows`, `fixture-isolated`) exist only inside the fake adapter.
- Docs/status updated: `docs/features/index.md`, this closeout
- Status surfaces reconciled: yes
- Summary metadata reviewed: yes
- Planning-only change? No
- Host deploy performed? No
