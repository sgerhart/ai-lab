# IWO-091 — AISVS agent quotas, tool-output checks, and stop

**Status:** Draft  
**Priority:** P2  
**Effort:** M  
**Owner:** human (operator)  
**Feature:** [FEAT-018](../features/FEAT-018-ai-security-platform.md)  
**Services / Areas:** platform, docs

## Problem

Privileged tools already wait for a human (AISVS 9.2.1, met). The other Level 1 agent rows are partial or gap: per-tool resource quotas, token and spend budgets, tool isolation, schema checks on tool output, and a stop that halts generation rather than only the lab run. See [the gap register](../security/aisvs-level-1.md).

## Decision Context

- Chosen approach: Enforce the budget fields that already exist but are ignored (`max_tokens`, and a documented time bound). Validate tool results against the schema the tool declared before they re-enter the model. Keep cancel as the operator stop, and record that it does not kill the Ollama process unless a later authorized IWO says so.
- Alternatives rejected: A new sandbox runtime in this IWO. Cryptographic agent identity (those C9 rows are Level 2 and Level 3).
- Assumptions: `RunBudget` stays the budget object (`conversation.py`).
- Open decisions: Numeric defaults for token and time budgets. Whether tool-output schema checks fail closed.

## What To Build / Fix

- Enforce `max_tokens` when set, with a unit test that stops the loop.
- Document per-tool timeout as the quota this lab actually has, and add one where a tool has none.
- Reject a tool result that does not match its declared schema, using a fake tool in tests.
- State in the register what cancel stops today. Do not claim it stops Studio Ollama unless the code does.
- Leave 9.2.1 met.

## Expected Change Surface

- Expected: `agent_loop.py`, `conversation.py`, tool result handling, tests, gap register
- Tests: unit tests with a fake backend. No live Ollama.
- Docs/status: gap register and this Closeout

## Out Of Scope

- Swarm kill switch (9.1.3 is Level 2).
- Changing Ollama’s process supervisor.
- Host deploy.

## Do NOT Change

- Do not copy AISVS prose into Git.
- Do not bypass `approval_required`.
- No secrets in Git. No host mutation.

## Acceptance Criteria

1. A unit test stops a run when the token budget is exhausted.
2. A unit test drops or rejects a tool result that fails schema validation.
3. Register rows 9.1.1, 9.1.2, 9.3.1, 9.3.2, and 9.6.1 match the code. 9.2.1 stays met.
4. `./scripts/validate-repo.sh` passes.

## Validation Plan

- Automated: unit tests and `./scripts/validate-repo.sh`
- Manual: read the 9.6.1 row and confirm it does not overclaim
- Evidence to include: test names and the 9.6.1 sentence

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none
- **May run on Air?** Yes — unit tests only

## Execution

- **Branch:** `iwo/091-aisvs-agent-bounds`
- **Risk tier:** P2
- **Pre-PR / pre-merge gate:** `./scripts/validate-repo.sh`
- **Depends on:** IWO-085, IWO-007
- **Human verification required:** Yes
- **Reviewer / approver:** human operator
- **Project status record:** `docs/features/index.md`
- **Other status surfaces:** `docs/security/aisvs-level-1.md`, `docs/security/agent-permissions.md`

## Closeout

- Verification evidence:
- Follow-ons filed:
- Residual risks:
- Docs/status updated:
- Status surfaces reconciled:
- Summary metadata reviewed:
- Planning-only change? No, once accepted and implemented
- Host deploy performed? No
