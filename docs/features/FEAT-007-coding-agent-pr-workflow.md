# FEAT-007 — Optional coding-agent and GitHub PR workflow

- **Status:** Specified (optional workload)
- **Created:** 2026-09-21
- **Owner:** human (operator)
- **GitHub issue:** [#8](https://github.com/sgerhart/ai-lab/issues/8)

## Purpose

Implement **approved Implementation Work Orders** on isolated branches and open
PRs. This is an **optional delegated workload** on the FEAT-010 harness—not the
core purpose of AI Lab.

## User workflow

Approved IWO → coding agent branch → tests → PR → **human** merge (never silent).

## Dependencies

FEAT-001, FEAT-010, FEAT-003 (often); ADR 0018. Prefer subscription-authorized
**official** coding clients (Claude Code / Codex) where appropriate; do not
abuse them as generic harness APIs (ADR 0038).

## Related

Local model profiles + read-only Coding Assistant land under
[FEAT-016](FEAT-016-local-coding-models-and-assistant.md) (IWO-055+). This Feature
remains the **write / PR delivery** track after hardening gates (IWO-058).

## Proposed IWOs

| ID | Title | Acceptance |
|----|-------|------------|
| IWO-055+ | See FEAT-016 (profiles, read-only, eval) | Before write/PR |
| IWO-058 (planned) | Isolated worktree + exact-action PR tools | Human merge required |

Historical note: earlier draft IWO-030/031 ids here were **reused** for scheduler
and background worker; do not revive them for coding.

## Out of scope

Self-merge; silent product-repo writes; replacing FEAT-010.

## Implementation status

| Layer | Status | Evidence |
|-------|--------|----------|
| Spec | Done | this file |
| Code | Partial | deterministic `development` plan |
| Live | No | — |
