# IWO-072 — Security Compute isolated network contract

**Status:** Draft  
**Priority:** P0  
**Effort:** M  
**Owner:** implementation agent  
**Feature:** FEAT-019  
**Services / Areas:** platform/security, docs, tests

## Problem

The Vise is unsafe unless the analysis guest network can be validated as isolated from trusted AI Lab and home networks.

## Decision Context

- Chosen approach: Treat network isolation as a precondition with fail-closed validation. The operator can create the isolated network. The analysis guest has exactly one NIC, on that network only. The security agent stays on the mini and uses the Proxmox API. The host's management interface and the isolated bridge do not route to each other.
- Alternatives rejected: a second NIC on the analysis guest facing a network the Macs can reach; putting the agent inside that guest; duplicate security stacks; implicit host mutation; unrestricted hypervisor credentials
- Assumptions: ADR 0043 is accepted before implementation. D-020 is Proxmox.
- Open decisions: bridge names, addresses, and the management endpoint stay operator-supplied (D-021, D-022). Do not invent them.

## What To Build / Fix

Define approved analysis-network resource metadata and checks: no Tailscale, no trusted-network attachment, expected NIC count, expected gateway/simulation policy, and optional controlled egress flag. Add provider validation hooks and job preflight result.

## Expected Change Surface

- Expected: platform/security, docs, tests
- Tests: add deterministic unit/contract tests; no live hypervisor mutation in normal CI.
- Docs/status: update feature/index status and this IWO closeout.

## Out Of Scope

Changing vSwitches, bridges, VLANs, firewall rules, routers, or host networking.

## Do NOT Change

Never invent or auto-create network names. Never treat provider-reported attachment alone as proof of routing isolation when stronger validation is available.

- No secrets in Git.
- No `0.0.0.0` committed binds.
- No host, hypervisor, network, model, or VM mutation without explicit authorization.
- Do not weaken existing approval gates.

## Acceptance Criteria

1. Job cannot become ready if network validation fails. 2. Trusted network identifiers can be denylisted. 3. Controlled egress defaults false. 4. Validation result is recorded as evidence.

## Validation Plan

- Automated: fail-closed cases using fake adapter.
- Manual: operator later supplies real network design for ESXi/Proxmox.
- Evidence: isolation report fixture.

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No by implementation alone; runtime use only after deployment authorization.
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** network read/validation; live mutation separately gated
- **May run on Air?** No

## Execution

- **Branch:** `iwo/072-security-compute-isolated-network-contract`
- **Risk tier:** P0
- **Pre-PR / pre-merge gate:** `./scripts/validate-repo.sh` plus targeted tests
- **Depends on:** IWO-071
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
