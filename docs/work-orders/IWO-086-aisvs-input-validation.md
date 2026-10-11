# IWO-086 — AISVS input validation for lab chat and agents

**Status:** Draft  
**Priority:** P2  
**Effort:** M  
**Owner:** human (operator)  
**Feature:** [FEAT-018](../features/FEAT-018-ai-security-platform.md)  
**Services / Areas:** platform, docs

## Problem

[AISVS Level 1](../security/aisvs-level-1.md) marks six input-validation requirements as gaps and one as partial. Studio chat and the agent loop accept steering text with no normalizer, no over-size reject, no character bound, and no harmful-content score. DefenseClaw screens IDE hooks on the Air only (requirement 2.1.3).

Identifiers: 2.1.1, 2.1.2, 2.1.3, 2.1.4, 2.1.5, 2.2.1, 2.2.2. Text stays in the upstream [C2 chapter](https://github.com/OWASP/AISVS/blob/main/1.0/en/0x10-C02-Input-Validation.md).

## Decision Context

- Chosen approach: A lab input gate in front of Studio chat and the agent loop. Record the result on the security event path from IWO-066. Leave DefenseClaw as the Air IDE control.
- Alternatives rejected: Copying AISVS sentences into Git. Routing every Studio prompt through the Air.
- Assumptions: ADR 0044 is the catalogue decision. This IWO starts only after a human accepts it.
- Open decisions: Which classifier, if any, runs locally on the Studio versus a deterministic rule list. Thresholds. What happens to an oversized prompt (reject, not truncate).

## What To Build / Fix

- Reject or mark input that fails a documented length limit, a documented character bound, and a normalization step, before it is sent to the model.
- Treat tool results and retrieved text as untrusted steering input on the same path as user text for 2.1.3.
- Add a harmful-content score for 2.2.1 and a note of how languages other than English are handled for 2.2.2.
- Update the C2 rows in `docs/security/aisvs-level-1.md` only when the control is in Git and tested.

## Expected Change Surface

- Expected: `platform/src/ai_lab_platform/` chat and agent entry, tests, the gap register
- Tests: unit tests with fixed strings. No live model call.
- Docs/status: gap register, this Closeout, `docs/features/index.md`

## Out Of Scope

- DefenseClaw rule-pack changes on the Air.
- Level 2 items 2.1.6, 2.1.7, and 2.2.3, and Level 3 items 2.1.8 and 2.2.4.
- Host deploy.

## Do NOT Change

- Do not copy AISVS requirement prose into Git.
- Do not weaken DefenseClaw or the approval gate.
- No secrets in Git. No `0.0.0.0` binds. No host mutation.

## Acceptance Criteria

1. A fixed over-long input and a fixed disallowed-content fixture are rejected or recorded as blocked before a model call, and tests show that.
2. Requirement 2.1.3 covers Studio chat, not only the Air IDE path.
3. The gap register rows for 2.1.1–2.2.2 match the code.
4. `./scripts/validate-repo.sh` and the new unit tests pass.

## Validation Plan

- Automated: new unit tests plus `./scripts/validate-repo.sh`
- Manual: one Studio chat attempt is not required for this IWO
- Evidence to include: test names and the updated register rows

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none
- **May run on Air?** Yes — client/dev only

## Execution

- **Branch:** `iwo/086-aisvs-input-validation`
- **Risk tier:** P2
- **Pre-PR / pre-merge gate:** `./scripts/validate-repo.sh`
- **Depends on:** IWO-085 register, ADR 0044
- **Human verification required:** Yes
- **Reviewer / approver:** human operator
- **Project status record:** `docs/features/index.md`
- **Other status surfaces:** `docs/security/aisvs-level-1.md`, FEAT-018

## Closeout

- Verification evidence:
- Follow-ons filed:
- Residual risks:
- Docs/status updated:
- Status surfaces reconciled:
- Summary metadata reviewed:
- Planning-only change? No, once accepted and implemented
- Host deploy performed? No
