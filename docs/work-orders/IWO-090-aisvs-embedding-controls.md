# IWO-090 — AISVS embedding scope and sensitive-field handling

**Status:** Draft  
**Priority:** P2  
**Effort:** S  
**Owner:** human (operator)  
**Feature:** [FEAT-018](../features/FEAT-018-ai-security-platform.md)  
**Services / Areas:** platform, docs

## Problem

Project search is scoped by `project_id`, and there is still one operator. `memory_write` waits for approval and then embeds the text as given. AISVS 8.1.1 is partial and 8.2.1 is a gap in [the gap register](../security/aisvs-level-1.md).

## Decision Context

- Chosen approach: Keep project scope as the namespace rule and test that a search cannot see another project’s points. Before embed, reject or mask a fixed set of sensitive patterns the lab already refuses to store, such as secret-shaped strings.
- Alternatives rejected: Inventing a second tenant. Embedding first and filtering later.
- Assumptions: Qdrant remains the store when configured (ADR 0024). Approval for `memory_write` stays (IWO-041).
- Open decisions: The exact pattern list. It must not include real secrets.

## What To Build / Fix

- A unit test that a project-scoped search does not return another project’s document.
- A pre-embed check that rejects a fixture containing a secret-shaped value, even if an approval flag is set.
- Update rows 8.1.1 and 8.2.1.

## Expected Change Surface

- Expected: retrieval or memory write path, tests, gap register
- Tests: unit tests with an in-memory or fake store. No live Qdrant required.
- Docs/status: gap register and this Closeout

## Out Of Scope

- Expiry and revocation (8.3 is Level 2 and Level 3).
- Multi-tenant product features.
- Host deploy.

## Do NOT Change

- Do not copy AISVS prose into Git.
- Do not put a real credential in a test fixture.
- Do not remove the `memory_write` approval.
- No host mutation.

## Acceptance Criteria

1. Cross-project search fails the leak test.
2. A secret-shaped fixture is not embedded.
3. Register rows match the tests. `./scripts/validate-repo.sh` passes.

## Validation Plan

- Automated: unit tests and `./scripts/validate-repo.sh`
- Manual: none
- Evidence to include: test names

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none
- **May run on Air?** Yes — unit tests only

## Execution

- **Branch:** `iwo/090-aisvs-embedding-controls`
- **Risk tier:** P2
- **Pre-PR / pre-merge gate:** `./scripts/validate-repo.sh`
- **Depends on:** IWO-085, IWO-041, IWO-060
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
