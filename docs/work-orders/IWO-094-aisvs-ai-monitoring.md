# IWO-094 — AISVS AI interaction log, injection alerts, and drift note

**Status:** Draft  
**Priority:** P2  
**Effort:** M  
**Owner:** human (operator)  
**Feature:** [FEAT-018](../features/FEAT-018-ai-security-platform.md)  
**Services / Areas:** platform, docs

## Problem

Agent runs are stored, and DefenseClaw reports IDE hook decisions. Studio chat has no structured interaction log, no jailbreak alert, and no input-drift signal. AISVS 12.1.1 and 12.2.1 are partial. 12.3.1 is a gap. 12.5.1 and 12.5.2 stay not applicable because the lab does not train or label. See [the gap register](../security/aisvs-level-1.md). General observability remains deferred ([ADR 0026](../decisions/0026-observability-deferred.md)).

## Decision Context

- Chosen approach: Extend the IWO-066 security event so a chat turn can emit session, model tag, and a decision of allow or block, without storing secret values. Drift is a documented gap with a defined input the lab will count later, not a metrics stack.
- Alternatives rejected: Standing up Prometheus or a SIEM. Sending chat text to the Air. Logging raw prompts into Git.
- Assumptions: Security events are not deployed with the live control plane until a separate restart is authorized.
- Open decisions: Retention of the new events. They follow the existing work-order retention note in `docs/security/overview.md`.

## What To Build / Fix

- An event payload for one chat turn: session id, model tag, and allow or block. Tests use fake text.
- A block reason when IWO-086’s input gate rejects a turn, if that gate exists. If IWO-086 is still Draft, this IWO records the event shape and a fake blocker.
- A short drift note in the register: what would be counted, and that it is not counted yet, unless this IWO implements a minimal counter in unit tests.
- Leave 12.5.1 and 12.5.2 not applicable.
- Do not claim ADR 0026 is withdrawn.

## Expected Change Surface

- Expected: `platform/src/ai_lab_platform/security/events.py`, tests, gap register
- Tests: unit tests. No live Postgres required if the store double is enough.
- Docs/status: gap register, `docs/security/event-envelope.md` if the payload grows, this Closeout

## Out Of Scope

- Deploying the control plane or a metrics service.
- Training-data lineage.
- Host deploy.

## Do NOT Change

- Do not copy AISVS prose into Git.
- Do not log secrets, full prompts, or full completions in a fixture that gets committed.
- Do not mark observability as live.
- No host mutation.

## Acceptance Criteria

1. A unit test records a chat-turn event with session and model tag and without a secret field.
2. The register rows 12.1.1, 12.2.1, and 12.3.1 match what the test actually does.
3. Rows 12.5.1 and 12.5.2 stay not applicable.
4. `./scripts/validate-repo.sh` passes.

## Validation Plan

- Automated: unit tests and `./scripts/validate-repo.sh`
- Manual: confirm the sample event has no prompt body
- Evidence to include: the sample event JSON from the test

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none
- **May run on Air?** Yes — unit tests only

## Execution

- **Branch:** `iwo/094-aisvs-ai-monitoring`
- **Risk tier:** P2
- **Pre-PR / pre-merge gate:** `./scripts/validate-repo.sh`
- **Depends on:** IWO-085, IWO-066, ADR 0026
- **Human verification required:** Yes
- **Reviewer / approver:** human operator
- **Project status record:** `docs/features/index.md`
- **Other status surfaces:** `docs/security/aisvs-level-1.md`, `docs/security/event-envelope.md`

## Closeout

- Verification evidence:
- Follow-ons filed:
- Residual risks:
- Docs/status updated:
- Status surfaces reconciled:
- Summary metadata reviewed:
- Planning-only change? No, once accepted and implemented
- Host deploy performed? No
