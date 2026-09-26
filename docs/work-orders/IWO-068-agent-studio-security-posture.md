# IWO-068 — Agent Studio security posture

**Status:** Draft  
**Priority:** P2  
**Effort:** M  
**Owner:** implementation agent  
**Feature:** FEAT-018  
**Services / Areas:** platform web, platform/security, docs, tests

## Problem

Agent Studio exposes model/tools/permissions but does not yet present a cohesive security posture for an agent definition.

## Decision Context

- Chosen approach: Render security posture from existing permissions plus the new MCP/security metadata; do not create a parallel permission system.
- Alternatives rejected: duplicate security stacks; implicit host mutation; unrestricted hypervisor credentials
- Assumptions: ADR 0043 is accepted before implementation.
- Open decisions: provider-specific details must come from operator-supplied ESXi/Proxmox inventory; do not invent endpoints, credentials, VLANs, bridges, port groups, or datastores.

## What To Build / Fix

Add agent security summary: runtime, models, MCP/tools, network class, filesystem/write class, secret access, approval-required actions, audit state, and warnings. Persist only canonical definition/policy data.

## Expected Change Surface

- Expected: platform web, platform/security, docs, tests
- Tests: add deterministic unit/contract tests; no live hypervisor mutation in normal CI.
- Docs/status: update feature/index status and this IWO closeout.

## Out Of Scope

Redesigning the entire Agent Studio layout.

## Do NOT Change

Do not let UI toggles bypass runtime policy.

- No secrets in Git.
- No `0.0.0.0` committed binds.
- No host, hypervisor, network, model, or VM mutation without explicit authorization.
- Do not weaken existing approval gates.

## Acceptance Criteria

1. Agent card/canvas shows effective security posture. 2. Changes map to supported definition/policy fields. 3. Privileged actions remain approval-gated. 4. UI labels distinguish intent from enforced policy.

## Validation Plan

- Automated: API/UI serialization tests.
- Manual: inspect coding-assistant and security-agent definitions.
- Evidence: screenshots optional, tests required.

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No by implementation alone; runtime use only after deployment authorization.
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none
- **May run on Air?** Yes

## Execution

- **Branch:** `iwo/068-agent-studio-security-posture`
- **Risk tier:** P2
- **Pre-PR / pre-merge gate:** `./scripts/validate-repo.sh` plus targeted tests
- **Depends on:** IWO-067
- **Human verification required:** Yes
- **Reviewer / approver:** human operator
- **Project status record:** `docs/features/index.md`
- **Other status surfaces:** `FEAT-018`, `docs/work-orders/README.md`

## Closeout

- Verification evidence:
- Follow-ons filed:
- Residual risks:
- Docs/status updated:
- Status surfaces reconciled:
- Summary metadata reviewed:
- Planning-only change? No
- Host deploy performed? No unless separately authorized and recorded
