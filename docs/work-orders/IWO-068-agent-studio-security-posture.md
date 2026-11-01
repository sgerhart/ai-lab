# IWO-068 — Agent Studio security posture

**Status:** Complete  
**Priority:** P2  
**Effort:** M  
**Owner:** operator  
**Feature:** FEAT-018  
**Services / Areas:** platform web, platform/security, docs, tests

## Problem

Agent Studio exposes model/tools/permissions but does not yet present a cohesive security posture for an agent definition.

## Decision Context

- Chosen approach: Render security posture from existing permissions plus the new MCP/security metadata; do not create a parallel permission system.
- Alternatives rejected: duplicate security stacks; implicit host mutation; unrestricted hypervisor credentials
- Assumptions: ADR 0043 is accepted before implementation.
- Open decisions: provider-specific details must come from operator-supplied ESXi/Proxmox inventory; do not invent endpoints, credentials, VLANs, bridges, port groups, or datastores.

## What Was Built

1. Added `platform/src/ai_lab_platform/security/posture.py` defining `AgentSecurityPosture` and `evaluate_agent_posture(...)`, calculating:
   - Isolation tiers (Tier 0 Vault, Tier 1 Read, Tier 2 Isolated Worktree).
   - Filesystem classes (`read-only`, `isolated-worktree`, `user-vault-scoped`, `reports-scoped`).
   - Network classes (`none`, `tailnet-client`, `egress-allowlist`, `loopback-only`).
   - Secret access boundaries (`none`, `gated-vault`).
   - Human approval gates (`apply_patch`, `git_commit`, `lab_memory_upsert`).
   - Permanent denials (`git_push`, `pr_create`, `deploy`, `host_mutate`, `rm_rf`).
   - Distinction between requested draft intent and enforced runtime policy.
2. Exposed security posture via control plane endpoints:
   - `GET /v1/agent-definitions/{id}/security-posture`
   - `POST /v1/agent-studio/security-posture`
   - Enriched `GET /v1/agent-definitions` and `POST /v1/agent-definitions` with `security_posture`.
3. Integrated security posture into Agent Studio UI:
   - Added posture badges (`Tier X · Class`) to presets and custom cards in `renderFleet`.
   - Added live "Security & Isolation Posture" card with metrics grid and policy banner in `renderBuilder`.
   - Replaced static placeholder with live `renderPermissions` Security Posture & Permissions Board.
4. Added comprehensive tests in `tests/test_agent_security_posture.py`.

## Acceptance Criteria

1. [x] Agent card/canvas shows effective security posture.
2. [x] Changes map to supported definition/policy fields.
3. [x] Privileged actions remain approval-gated.
4. [x] UI labels distinguish intent from enforced policy.

## Validation Plan

- Automated: `python3 -m unittest tests/test_agent_security_posture.py -v` (10 tests passing).
- Manual: inspect coding-assistant and security-agent definitions.
- Evidence: clean unit and contract test execution.

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none
- **May run on Air?** Yes

## Closeout

- Verification evidence: `tests/test_agent_security_posture.py`, `tests/test_agent_studio_shell.py`, `tests/test_security_platform.py` all passing.
- Follow-ons filed: IWO-069 (Security Center expansion).
- Residual risks: none; zero network imports in `security/` package preserved.
- Docs/status updated: `docs/features/FEAT-018-ai-security-platform.md`, `docs/features/index.md`, `docs/work-orders/README.md`.
- Status surfaces reconciled: Yes.
- Summary metadata reviewed: Yes.
- Planning-only change? No.
- Host deploy performed? No.

