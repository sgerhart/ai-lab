# IWO-067 — MCP registry and governed capabilities

**Status:** Complete (unit; not deployed)  
**Priority:** P1  
**Effort:** L  
**Owner:** implementation agent  
**Feature:** FEAT-018  
**Services / Areas:** platform/mcp, platform/security, docs, tests

## Problem

MCP servers are supported in two directions but are not modeled as governed resources with capability metadata, consumers, permission classes, and security state.

## Decision Context

- Chosen approach: Introduce a control-plane MCP registry separate from transport code.
- Alternatives rejected: duplicate security stacks; implicit host mutation; unrestricted hypervisor credentials
- Assumptions: ADR 0043 is accepted before implementation.
- Open decisions: provider-specific details must come from operator-supplied ESXi/Proxmox inventory; do not invent endpoints, credentials, VLANs, bridges, port groups, or datastores.

## What To Build / Fix

Add MCP server/resource records, capability discovery metadata, agent bindings, credential reference IDs, network policy metadata, audit hooks, and read APIs. Preserve deny-unlisted behavior. Provide migration/default entries for existing lab MCP where appropriate.

## Expected Change Surface

- Expected: platform/mcp, platform/security, docs, tests
- Tests: add deterministic unit/contract tests; no live hypervisor mutation in normal CI.
- Docs/status: update feature/index status and this IWO closeout.

## Out Of Scope

Installing third-party MCP servers or granting credentials.

## Do NOT Change

Do not auto-trust discovered MCP servers; discovery is not authorization.

- No secrets in Git.
- No `0.0.0.0` committed binds.
- No host, hypervisor, network, model, or VM mutation without explicit authorization.
- Do not weaken existing approval gates.

## Acceptance Criteria

1. Registry lists MCP servers and capabilities. 2. Agent bindings are explicit. 3. Unlisted capabilities remain denied. 4. Security events are emitted for binding/use decisions.

## Validation Plan

- Automated: registry and policy tests.
- Manual: existing lab MCP still follows deny-unlisted rules.
- Evidence: API fixture and tests.

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No by implementation alone; runtime use only after deployment authorization.
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none
- **May run on Air?** Yes

## Execution

- **Branch:** `iwo/067-mcp-registry-and-governed-capabilities`
- **Risk tier:** P1
- **Pre-PR / pre-merge gate:** `./scripts/validate-repo.sh` plus targeted tests
- **Depends on:** IWO-065,IWO-066
- **Human verification required:** Yes
- **Reviewer / approver:** human operator
- **Project status record:** `docs/features/index.md`
- **Other status surfaces:** `FEAT-018`, `docs/work-orders/README.md`

## Closeout

- Verification evidence: `tests/test_security_platform.py` denies an unlisted `ai-lab` binding, allows only an explicit capability, and `GET /v1/security/mcp` keeps `deny-unlisted` (2026-09-26).
- Follow-ons filed: none. Bindings are process memory; a durable binding table is later work if the operator wants them to survive restart.
- Residual risks: the catalog names the lab MCP server and does not authorize it. `platform/mcp/allowlist.json` is still empty.
- Docs/status updated: this file, FEAT-018, feature and work-order indexes
- Status surfaces reconciled: yes
- Summary metadata reviewed: yes
- Planning-only change? No
- Host deploy performed? No
