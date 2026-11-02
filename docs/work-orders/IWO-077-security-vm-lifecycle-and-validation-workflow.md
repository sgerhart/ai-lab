# IWO-077 — Security VM lifecycle and validation workflow

**Status:** Implemented  
**Priority:** P0  
**Effort:** L  
**Owner:** implementation agent  
**Feature:** FEAT-020  
**Services / Areas:** platform/orchestrator, platform/security, agents, docs, tests

## Problem

The security agent needs a deterministic orchestration graph so failures cannot skip validation or cleanup.

## Decision Context

- Chosen approach: Implement lifecycle as a resumable state machine through existing LangGraph/approval patterns.
- Alternatives rejected: duplicate security stacks; implicit host mutation; unrestricted hypervisor credentials
- Assumptions: ADR 0043 is accepted before implementation.
- Open decisions: provider-specific details must come from operator-supplied ESXi/Proxmox inventory; do not invent endpoints, credentials, VLANs, bridges, port groups, or datastores.

## What To Build / Fix

Add steps: inventory→template_validate→network_validate→clone_request→boot→guest_ready→benign_validation→execution_approval→analysis→collect→shutdown→destroy/revert→residual_check→report. Add compensating cleanup for failures and explicit blocked state.

## Expected Change Surface

- Expected: platform/orchestrator, platform/security, agents, docs, tests
- Tests: add deterministic unit/contract tests; no live hypervisor mutation in normal CI.
- Docs/status: update feature/index status and this IWO closeout.

## Out Of Scope

Automatic untrusted-sample execution or host/network configuration.

## Do NOT Change

Cleanup must be attempted on all post-clone failures; failure to prove cleanup leaves job blocked/incident state, not success.

- No secrets in Git.
- No `0.0.0.0` committed binds.
- No host, hypervisor, network, model, or VM mutation without explicit authorization.
- Do not weaken existing approval gates.

## Acceptance Criteria

1. Fake-provider workflow covers success and every major failure point. 2. No transition bypasses approval. 3. Cleanup is idempotent. 4. Residual check gates completion. 5. Resume after process restart is supported by existing durable patterns.

## Validation Plan

- Automated: state-machine matrix and restart/resume tests (`tests/test_security_lifecycle.py`).
- Manual: inspect audit trace.
- Evidence: transition logs.

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No by implementation alone; runtime use only after deployment authorization.
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** approval service; hypervisor lifecycle when deployed
- **May run on Air?** No

## Execution

- **Branch:** `main`
- **Risk tier:** P0
- **Pre-PR / pre-merge gate:** `./scripts/validate-repo.sh` plus targeted tests
- **Depends on:** IWO-070,IWO-071,IWO-072,IWO-073
- **Human verification required:** Yes
- **Reviewer / approver:** human operator
- **Project status record:** `docs/features/index.md`
- **Other status surfaces:** `FEAT-020`, `docs/work-orders/README.md`

## Closeout

- Verification evidence: `tests/test_security_lifecycle.py` passed (8 tests in 0.145s) covering 14-step benign and untrusted paths, pre/post clone failure compensating cleanups, idempotent cleanup, residual check gated blocked incident states, and LangGraph process restart with interrupt/resume. `python3 -m unittest discover -s tests -v` passed all 474 tests.
- Follow-ons filed: IWO-074 (VISE evidence collection pipeline), IWO-078 (hypervisor test harness & benign e2e validation).
- Residual risks: Live ESXi/Proxmox deployment remains unauthorized and requires operator-supplied inventory, endpoint, and isolated network parameters.
- Docs/status updated: `docs/features/FEAT-020-security-compute-agent.md`, `docs/features/index.md`, `docs/roadmap.md`.
- Status surfaces reconciled: Yes
- Summary metadata reviewed: Yes
- Planning-only change? No
- Host deploy performed? No unless separately authorized and recorded
