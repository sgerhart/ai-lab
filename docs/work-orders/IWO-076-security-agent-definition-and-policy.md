# IWO-076 — Security agent definition and policy

**Status:** Implemented  
**Priority:** P1  
**Effort:** M  
**Owner:** implementation agent  
**Feature:** FEAT-020  
**Services / Areas:** agents, platform/security, docs, tests

## Problem

AI Lab needs a dedicated identity for security-compute operations instead of reusing coding or lab-operations permissions.

## Decision Context

- Chosen approach: Add a `security` agent with explicit read, lifecycle, evidence, and prohibited operation classes.
- Alternatives rejected: duplicate security stacks; implicit host mutation; unrestricted hypervisor credentials
- Assumptions: ADR 0043 is accepted before implementation.
- Open decisions: provider-specific details must come from operator-supplied ESXi/Proxmox inventory; do not invent endpoints, credentials, VLANs, bridges, port groups, or datastores.

## What To Build / Fix

Create `agents/security` definition, README, policy file, catalog entry, Agent Studio template metadata, and tool bindings to the bounded hypervisor/Vise APIs. Read-only validation is separate from approval-gated lifecycle.

## Expected Change Surface

- Expected: agents, platform/security, docs, tests
- Tests: add deterministic unit/contract tests; no live hypervisor mutation in normal CI.
- Docs/status: update feature/index status and this IWO closeout.

## Out Of Scope

Granting raw ESXi/Proxmox admin, SSH, arbitrary shell, or network mutation.

## Do NOT Change

Agent policy must not include generic host administration or trusted-network attachment.

- No secrets in Git.
- No `0.0.0.0` committed binds.
- No host, hypervisor, network, model, or VM mutation without explicit authorization.
- Do not weaken existing approval gates.

## Acceptance Criteria

1. Security agent can call only listed security tools. 2. Read vs lifecycle permissions are distinguishable. 3. Untrusted execution permission is approval-gated. 4. Policy tests deny generic hypervisor/admin actions.

## Validation Plan

- Automated: policy and tool-runtime denial tests (`tests/test_security_agent.py`).
- Manual: inspect effective Agent Studio posture.
- Evidence: permission matrix.

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No by implementation alone; runtime use only after deployment authorization.
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** bounded hypervisor lifecycle tools after deploy
- **May run on Air?** No

## Execution

- **Branch:** `main`
- **Risk tier:** P1
- **Pre-PR / pre-merge gate:** `./scripts/validate-repo.sh` plus targeted tests
- **Depends on:** IWO-067,IWO-071
- **Human verification required:** Yes
- **Reviewer / approver:** human operator
- **Project status record:** `docs/features/index.md`
- **Other status surfaces:** `FEAT-020`, `docs/work-orders/README.md`

## Closeout

- Verification evidence: `tests/test_security_agent.py` passed (7 tests in 0.006s) covering AC 1 (only listed security tools callable; unlisted tools dropped), AC 2 (read vs lifecycle permissions distinguishable; read tools recognized in READ_TOOLS and not privileged; lifecycle tools flagged as privileged), AC 3 (untrusted execution strictly approval-gated), AC 4 (generic hypervisor/admin actions denied; posture evaluation produces tier 2, isolated-vm, isolated-bridge, with warnings on denied tools), and local deterministic plan execution (inventory + preflight run without VM creation). Full test suite passed 487 tests in 10.037s.
- Follow-ons filed: IWO-074 (cybersecurity VISE evidence collection pipeline).
- Residual risks: Live ESXi/Proxmox deployment remains unauthorized and requires operator-supplied inventory, endpoint, and isolated network parameters.
- Docs/status updated: `docs/features/FEAT-020-security-compute-agent.md`, `docs/features/index.md`, `docs/work-orders/README.md`, `docs/roadmap.md`.
- Status surfaces reconciled: Yes
- Summary metadata reviewed: Yes
- Planning-only change? No
- Host deploy performed? No unless separately authorized and recorded
