# FEAT-009 — Scheduled personal and lab-operations agents

- **Status:** Partial (IWO-030 schedule tick in Git)
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
| [IWO-030](../work-orders/IWO-030-personal-agent-scheduler.md) | Schedule tick API + cron match | Due definition starts run; no double-fire |
| IWO-051 | Diff/report format | No write tools |
| IWO-052 | LaunchAgent / host timer (deploy-gated) | Minute tick on mini |

## Out of scope

Auto-restart hosts; auto `compose down -v`.

## Implementation status

| Layer | Status |
|-------|--------|
| Spec | Done |
| Code | Partial — `POST /v1/scheduler/tick`, cron on agent definitions, unit tests |
| Live | Tick available after sync; host timer **not** installed |
