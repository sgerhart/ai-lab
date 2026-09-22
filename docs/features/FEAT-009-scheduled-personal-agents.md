# FEAT-009 — Scheduled personal and lab-operations agents

- **Status:** Specified
- **Created:** 2026-09-21
- **Owner:** human (operator)
- **GitHub issue:** [#10](https://github.com/sgerhart/ai-lab/issues/10)

## Purpose

Periodic personal/lab-operations tasks on the mini (health reports, reminders)
without silent remediation. Builds on FEAT-010 + FEAT-002.

## Dependencies

FEAT-002, FEAT-010; lab-ops policy remains read-only until ADR + policy change.

## Proposed IWOs

| ID | Title | Acceptance |
|----|-------|------------|
| IWO-050 | Scheduler → runtime WO | Creates run + report |
| IWO-051 | Diff/report format | No write tools |

## Out of scope

Auto-restart hosts; auto `compose down -v`.

## Implementation status

| Layer | Status |
|-------|--------|
| Spec | Done |
| Code | Partial (on-demand tools; no scheduler) |
| Live | No scheduler |
