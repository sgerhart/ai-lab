# FEAT-007 — Optional coding-agent and GitHub PR workflow

- **Status:** Specified for pull-request delivery. Isolated patch/commit is FEAT-016, not this Feature.
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

Local model profiles, read-only inspect, and isolated patch/commit land under
[FEAT-016](FEAT-016-local-coding-models-and-assistant.md). This Feature remains
**pull-request delivery**. `git_push` and PR tools are still denied.

## Proposed IWOs

| ID | Title | Acceptance |
|----|-------|------------|
| IWO-055+ | See FEAT-016 (profiles, read tools, isolated patch/commit) | Done in that Feature except eval |
| Later | Pull-request tools | Human merge required. Not started |

Historical note: earlier draft IWO-030/031 ids here were **reused** for scheduler
and background worker; do not revive them for coding.

## Out of scope

Self-merge; silent product-repo writes; replacing FEAT-010.

## Implementation status

| Layer | Status | Evidence |
|-------|--------|----------|
| Spec | Done | this file |
| Code | Not started for PR tools | Isolated patch/commit is FEAT-016, not a PR |
| Live | No | — |
