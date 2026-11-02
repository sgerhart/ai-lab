# IWO-074 — Vise evidence collection pipeline

**Status:** Implemented  
**Priority:** P1  
**Effort:** L  
**Owner:** implementation agent  
**Feature:** FEAT-019  
**Services / Areas:** platform/security, docs, tests

## Problem

AI analysis should consume structured evidence rather than directly trusting or mounting an infected guest.

## Decision Context

- Chosen approach: Collect and normalize evidence through bounded collectors and reference it using the common evidence model.
- Alternatives rejected: duplicate security stacks; implicit host mutation; unrestricted hypervisor credentials
- Assumptions: ADR 0043 is accepted before implementation.
- Open decisions: provider-specific details must come from operator-supplied ESXi/Proxmox inventory; do not invent endpoints, credentials, VLANs, bridges, port groups, or datastores.

## What To Build / Fix

Implement collector contracts for process tree, filesystem/registry delta, DNS/network metadata, PCAP reference, hashes, static metadata, YARA/tool results, screenshots, and optional memory-analysis references. Add sanitation/redaction and quarantine metadata.

## Expected Change Surface

- Expected: platform/security, docs, tests
- Tests: add deterministic unit/contract tests; no live hypervisor mutation in normal CI.
- Docs/status: update feature/index status and this IWO closeout.

## Out Of Scope

Automatically exporting suspicious executables or memory blobs onto trusted Mac filesystems.

## Do NOT Change

Raw suspicious artifacts require an explicit quarantine/export policy and are not embedded in database rows.

- No secrets in Git.
- No `0.0.0.0` committed binds.
- No host, hypervisor, network, model, or VM mutation without explicit authorization.
- Do not weaken existing approval gates.

## Acceptance Criteria

1. Collector fixtures normalize to evidence schema. 2. Missing collectors degrade gracefully. 3. Suspicious binary bytes are not returned by default API. 4. Evidence can be summarized for an LLM without granting guest access.

## Validation Plan

- Automated: collector fixture tests.
- Manual: benign fixture evidence review.
- Evidence: sample report.

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No by implementation alone; runtime use only after deployment authorization.
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** guest collector tools later
- **May run on Air?** No

## Execution

- **Branch:** `iwo/074-vise-evidence-collection-pipeline`
- **Risk tier:** P1
- **Pre-PR / pre-merge gate:** `./scripts/validate-repo.sh` plus targeted tests
- **Depends on:** IWO-066,IWO-070
- **Human verification required:** Yes
- **Reviewer / approver:** human operator
- **Project status record:** `docs/features/index.md`
- **Other status surfaces:** `FEAT-019`, `docs/work-orders/README.md`

## Closeout

- Verification evidence: `python3 -m unittest tests/test_evidence_pipeline.py -v` (6 tests passed, covering schema normalization, graceful degradation, binary byte rejection, LLM briefing generation, and ViseStore integration); full test suite passed (493 tests); `./scripts/preflight.sh && ./scripts/validate-repo.sh && ./tests/test_structure.sh` passed.
- Follow-ons filed: IWO-075 (Vise analyst reporting and findings workflow)
- Residual risks: None in unit mode; live analysis requires operator-authorized deployment and hypervisor inventory.
- Docs/status updated: `docs/features/index.md`, `docs/features/FEAT-019-cybersecurity-vise.md`, `docs/work-orders/README.md`, `docs/roadmap.md`.
- Status surfaces reconciled: Yes
- Summary metadata reviewed: Yes
- Planning-only change? No
- Host deploy performed? No unless separately authorized and recorded
