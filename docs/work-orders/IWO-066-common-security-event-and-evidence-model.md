# IWO-066 — Common security event and evidence model

**Status:** Complete (unit; not deployed)  
**Priority:** P1  
**Effort:** M  
**Owner:** implementation agent  
**Feature:** FEAT-018  
**Services / Areas:** platform, docs, tests

## Problem

Security and analysis signals need one schema so runs, agents, MCP calls, Antares results, Vise jobs, and approvals can be correlated.

## Decision Context

- Chosen approach: Use a normalized event/evidence envelope stored through existing durable control-plane patterns.
- Alternatives rejected: duplicate security stacks; implicit host mutation; unrestricted hypervisor credentials
- Assumptions: ADR 0043 is accepted before implementation.
- Open decisions: provider-specific details must come from operator-supplied ESXi/Proxmox inventory; do not invent endpoints, credentials, VLANs, bridges, port groups, or datastores.

## What To Build / Fix

Define event IDs, subject/resource identity, run/job correlation, severity/classification, evidence references, timestamps, provider/source, approval linkage, retention metadata, and serialization. Add APIs/store adapters without logging secrets or raw malware by default.

## Expected Change Surface

- Expected: platform, docs, tests
- Tests: add deterministic unit/contract tests; no live hypervisor mutation in normal CI.
- Docs/status: update feature/index status and this IWO closeout.

## Out Of Scope

Full SIEM stack, long-term object storage, or malware detonation.

## Do NOT Change

Do not duplicate conversation/work-order stores unnecessarily; reference existing IDs.

- No secrets in Git.
- No `0.0.0.0` committed binds.
- No host, hypervisor, network, model, or VM mutation without explicit authorization.
- Do not weaken existing approval gates.

## Acceptance Criteria

1. Events correlate to agent/run/tool/job. 2. Evidence references can point to external/quarantined storage without embedding bytes. 3. Redaction tests pass. 4. Stable JSON schema documented.

## Validation Plan

- Automated: schema, redaction, round-trip tests.
- Manual: inspect representative Antares/MCP/Vise examples.
- Evidence: fixtures.

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No by implementation alone; runtime use only after deployment authorization.
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none
- **May run on Air?** Yes

## Execution

- **Branch:** `iwo/066-common-security-event-and-evidence-model`
- **Risk tier:** P1
- **Pre-PR / pre-merge gate:** `./scripts/validate-repo.sh` plus targeted tests
- **Depends on:** IWO-065
- **Human verification required:** Yes
- **Reviewer / approver:** human operator
- **Project status record:** `docs/features/index.md`
- **Other status surfaces:** `FEAT-018`, `docs/work-orders/README.md`

## Closeout

- Verification evidence: `tests/test_security_platform.py` round-trip, redaction, sqlite filter, and authenticated `POST /v1/security/events` (2026-09-26).
- Follow-ons filed: none. Quarantine location remains D-023.
- Residual risks: the Postgres table is in `schema.sql` and is created on the next control-plane start. This change did not restart the mini.
- Docs/status updated: this file, `docs/security/event-envelope.md`, FEAT-018, feature and work-order indexes
- Status surfaces reconciled: yes
- Summary metadata reviewed: yes
- Planning-only change? No
- Host deploy performed? No
