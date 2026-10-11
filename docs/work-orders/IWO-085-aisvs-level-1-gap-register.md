# IWO-085 — AISVS 1.0 Level 1 gap register

**Status:** Review  
**Priority:** P2  
**Effort:** S  
**Owner:** human (operator)  
**Feature:** [FEAT-018](../features/FEAT-018-ai-security-platform.md)  
**Services / Areas:** docs

## Problem

The security stack has tools and a platform module, and no shared list of which OWASP AISVS 1.0 requirements those tools cover. Without that list, later security work cannot tell a met control from a gap, and a chat summary of the mapping will drift from the files.

## Decision Context

- Chosen approach: A gap register in `docs/security/` that cites AISVS 1.0 requirement IDs and describes lab evidence in our own words. Decision record: [ADR 0044](../decisions/0044-adopt-aisvs-level-1.md) (Proposed).
- Alternatives rejected: Pasting AISVS requirement sentences into Git. Standing up AISVS as a runtime service. Claiming the lab is verified.
- Assumptions: The catalogue to map is AISVS 1.0 in [OWASP/AISVS](https://github.com/OWASP/AISVS) `1.0/`, not the in-progress `1.01-dev` tree. Upstream IDs use the form `1.1.1`.
- Open decisions: Which gaps become follow-on work orders. Whether a later ADR raises the bar to Level 2. Whether to assess ASVS at the matching level.

## What To Build / Fix

The register is written at `docs/security/aisvs-level-1.md`. ADR 0044 is still Proposed. This section is the contract that file satisfies:

- Add `docs/security/aisvs-level-1.md`.
- For each AISVS 1.0 **Level 1** requirement, one row: requirement ID, chapter, lab evidence (paths, ADRs, IWOs), and status `met`, `partial`, `gap`, or `not applicable`.
- Write the evidence sentence here. Link the upstream chapter for the requirement text.
- Point `docs/security/overview.md` at the register.
- Update FEAT-018 and `docs/features/index.md` so the register is visible and still not called a certification.

Surfaces the register must account for, from the current tree:

- Agents and approvals: `docs/security/agent-permissions.md`, ADR 0018
- MCP: IWO-067, IWO-079, IWO-080, DefenseClaw (FEAT-014)
- Models: IWO-055 catalog and roles; `WO-006` refuses training pulls
- Retrieval and memory: ADR 0024, IWO-041, IWO-060, IWO-082, IWO-083, IWO-084
- Events: IWO-066, `docs/security/event-envelope.md`; observability remains deferred (ADR 0026)
- Isolation: ADR 0017; hostile workloads only via FEAT-019 / ADR 0043, which is not live

## Expected Change Surface

- Expected: `docs/security/aisvs-level-1.md`, `docs/security/overview.md`, FEAT-018, `docs/features/index.md`
- Tests: `./scripts/validate-repo.sh` if the new doc is on a checked path. No new runtime tests in this IWO.
- Docs/status: this IWO’s Closeout after the register exists

## Out Of Scope

- Implementing missing controls (model signature checks, output classifiers, drift detection, ASVS assessment).
- Level 2 and Level 3 as acceptance criteria. Mention an existing control if it is already in the tree.
- Security Center UI (IWO-069), Agent Studio posture (IWO-068), and Vise implementation.
- Host deploy, model pulls, firewall, SSH, or Tailscale changes.

## Do NOT Change

- Do not copy AISVS or ASVS requirement prose into this repository (ADR 0021, CC BY-SA 4.0).
- Do not vendor the AISVS PDF or markdown tree.
- Do not mark the lab AISVS-verified or ASVS-verified.
- Do not replace DefenseClaw, Antares, Vise, `policy.py`, or `approvals.py`.
- No secrets in Git. No `0.0.0.0` binds. No host mutation from this IWO.

## Acceptance Criteria

1. `docs/security/aisvs-level-1.md` lists every AISVS 1.0 Level 1 requirement ID, with status and lab evidence written in this repo’s words.
2. A reader can open the upstream AISVS 1.0 chapter from the register without the requirement sentence living in Git.
3. FEAT-018 and the security overview link the register and still say the lab is not certified.
4. `./scripts/validate-repo.sh` passes.

## Validation Plan

- Automated: `./scripts/validate-repo.sh`
- Manual: Count Level 1 IDs in upstream `1.0/` against rows in the register. Read every `met` row and confirm the cited file exists.
- Evidence to include: the count, and the list of `met` rows checked.

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none
- **May run on Air?** Yes — docs only

## Execution

- **Branch:** `iwo/085-aisvs-level-1-gap-register`
- **Risk tier:** P2
- **Pre-PR / pre-merge gate:** `./scripts/validate-repo.sh`
- **Depends on:** ADR 0044 accepted
- **Human verification required:** Yes — read the one `met` row (9.2.1) and accept ADR 0044 before this IWO moves from Review to Complete
- **Reviewer / approver:** human operator
- **Project status record:** `docs/features/index.md`
- **Other status surfaces:** FEAT-018, `docs/work-orders/README.md`, `docs/decisions/README.md`

## Closeout

- Verification evidence: `docs/security/aisvs-level-1.md` lists 51 Level 1 identifiers (C5 has none). Counts in that file: 1 met (9.2.1), 19 partial, 24 gap, 7 not applicable. The single met row cites ADR 0018, `agent_loop.py`, and `approvals.py`. Requirement sentences were not copied. `./scripts/validate-repo.sh` is the check for this closeout.
- Follow-ons filed: IWO-086 through IWO-094, all Draft. C1 and the C5 Level 1 set need no follow-on. 3.4.1, 4.3.1, 10.2.3, 10.3.1, 12.5.1, and 12.5.2 have no implementation IWO.
- Residual risks: ADR 0044 is still Proposed. A met row is not a certification. The operator has not yet read the met row. ASVS was not assessed.
- Docs/status updated: gap register, security overview, security plane, architecture overview, FEAT-018, feature index, work-order index, ADR 0044 consequences
- Status surfaces reconciled: yes
- Summary metadata reviewed: yes
- Planning-only change? The register is documentation. Follow-on IWOs are Draft and do not change runtime code.
- Host deploy performed? No
