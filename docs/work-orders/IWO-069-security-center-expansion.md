# IWO-069 — Security Center expansion

**Status:** Complete  
**Priority:** P2  
**Effort:** L  
**Owner:** implementation agent  
**Feature:** FEAT-018  
**Services / Areas:** platform web, platform/security, docs, tests

## Problem

The current Security surface is tool-oriented and should become the unified operator view for providers, findings, Vise, MCP/tool posture, and audit.

## Decision Context

- Chosen approach: Expand the existing Security UI rather than adding a separate security application.
- Alternatives rejected: duplicate security stacks; implicit host mutation; unrestricted hypervisor credentials
- Assumptions: ADR 0043 is accepted before implementation.
- Open decisions: provider-specific details must come from operator-supplied ESXi/Proxmox inventory; do not invent endpoints, credentials, VLANs, bridges, port groups, or datastores.

## What To Build / Fix

Add overview and sections for providers, agent posture, MCP/tools, Antares, Security Compute, Vise jobs, findings/evidence, audit, and policies. Initially sections may be read-only when backends are incomplete.

## Expected Change Surface

- Expected: platform web, platform/security, docs, tests
- Tests: add deterministic unit/contract tests; no live hypervisor mutation in normal CI.
- Docs/status: update feature/index status and this IWO closeout.

## Out Of Scope

Deploying DefenseClaw config changes or hypervisor mutations.

## Do NOT Change

Do not expose secret values or raw suspicious binaries.

- No secrets in Git.
- No `0.0.0.0` committed binds.
- No host, hypervisor, network, model, or VM mutation without explicit authorization.
- Do not weaken existing approval gates.

## Acceptance Criteria

1. Security page aggregates provider/status data. 2. Missing providers show unavailable/stale without breaking page. 3. Findings/evidence link to correlated job/run IDs. 4. No secret values rendered.

## Validation Plan

- Automated: page/API tests.
- Manual: browser pass after separately authorized deploy.
- Evidence: tests and route list.

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No by implementation alone; runtime use only after deployment authorization.
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none
- **May run on Air?** Yes

## Execution

- **Branch:** `iwo/069-security-center-expansion`
- **Risk tier:** P2
- **Pre-PR / pre-merge gate:** `./scripts/validate-repo.sh` plus targeted tests
- **Depends on:** IWO-066,IWO-067
- **Human verification required:** Yes
- **Reviewer / approver:** human operator
- **Project status record:** `docs/features/index.md`
- **Other status surfaces:** `FEAT-018`, `docs/work-orders/README.md`

## Closeout

- Verification evidence:
  - Route added: `GET /v1/security/overview` aggregating providers (DefenseClaw, Antares, Vise, MCP, Hypervisor), metrics, recent events, Vise jobs, MCP catalog, and system policies.
  - Resilience: Missing providers (Antares without URL, DefenseClaw without report, Hypervisor without inventory) show `unavailable` or `stale` without breaking the endpoint.
  - Correlation: Findings and evidence events correlate to clickable `job_id` and `run_id` links with `EvidenceRef` tags and inspection modal.
  - Zero secrets: All event details pass through `redact()`. Raw payload keys are refused (400) and passwords/tokens masked (`[redacted]`).
  - Unit & contract tests: `tests/test_security_center.py` (5 tests passing; full suite 454 tests passed).
  - Repo validator: `./scripts/validate-repo.sh` passed (`RESULT: OK`).
- Follow-ons filed: IWO-072 (Security Compute isolated network contract), IWO-073 (Security VM template contract).
- Residual risks: Live ESXi/Proxmox hypervisor mutation refused until operator supplies inventory (ADR 0043).
- Docs/status updated: `docs/work-orders/IWO-069-security-center-expansion.md`, `docs/features/FEAT-018-ai-security-platform.md`, `docs/features/index.md`, `docs/work-orders/README.md`.
- Status surfaces reconciled: Yes.
- Summary metadata reviewed: Yes.
- Planning-only change? No
- Host deploy performed? No unless separately authorized and recorded

