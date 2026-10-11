# IWO-089 — AISVS output bounds, safety, and citation checks

**Status:** Draft  
**Priority:** P2  
**Effort:** M  
**Owner:** human (operator)  
**Feature:** [FEAT-018](../features/FEAT-018-ai-security-platform.md)  
**Services / Areas:** platform, docs

## Problem

Chat shows model text as returned. Step budgets stop the tool loop and do not cap one completion. Nothing classifies a harmful response. Retrieval can attach sources, and nothing checks that a citation string came from retrieval metadata. AISVS Level 1 rows 7.1.1, 7.1.2, 7.3.1, 7.4.1, and 7.4.2 in [the gap register](../security/aisvs-level-1.md).

## Decision Context

- Chosen approach: Bound completion length in the lab request. For grounded turns, drop citation strings that are not in the retrieval payload. Record a harmful-response decision with a deterministic fixture in tests before any live classifier is chosen.
- Alternatives rejected: Asking the model to police its own citations. Treating the IWO-057 bench as an output safety test.
- Assumptions: Grounded chat already receives source text (IWO-082).
- Open decisions: The classifier implementation. A fixture that represents a blocked class is enough for the first test.

## What To Build / Fix

- A max output bound enforced by the lab, distinct from `max_steps`.
- For turns that include retrieval sources, keep only attributions present in that metadata.
- A response check with a fixed blocked fixture, and a pass-through fixture.
- Update the five C7 rows.

## Expected Change Surface

- Expected: chat response path, `chat_grounding.py` or `retrieval.py`, tests, gap register
- Tests: unit tests. No live model.
- Docs/status: gap register and this Closeout

## Out Of Scope

- Hallucination scoring beyond the citation check (7.2 is Level 2 and Level 3).
- Image and audio outputs.
- Host deploy.

## Do NOT Change

- Do not copy AISVS prose into Git.
- Do not invent citations when retrieval returns nothing. That policy stays.
- No secrets in Git. No host mutation.

## Acceptance Criteria

1. A unit test shows an over-long completion is cut off or refused by the lab bound.
2. A unit test shows a citation that is not in the retrieval payload is removed.
3. A unit test shows the blocked fixture does not reach the caller as a normal answer.
4. The five register rows match the code. `./scripts/validate-repo.sh` passes.

## Validation Plan

- Automated: unit tests and `./scripts/validate-repo.sh`
- Manual: none required for the fixtures
- Evidence to include: test names and register rows

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none
- **May run on Air?** Yes — client/dev only

## Execution

- **Branch:** `iwo/089-aisvs-output-controls`
- **Risk tier:** P2
- **Pre-PR / pre-merge gate:** `./scripts/validate-repo.sh`
- **Depends on:** IWO-085, IWO-082
- **Human verification required:** Yes
- **Reviewer / approver:** human operator
- **Project status record:** `docs/features/index.md`
- **Other status surfaces:** `docs/security/aisvs-level-1.md`

## Closeout

- Verification evidence:
- Follow-ons filed:
- Residual risks:
- Docs/status updated:
- Status surfaces reconciled:
- Summary metadata reviewed:
- Planning-only change? No, once accepted and implemented
- Host deploy performed? No
