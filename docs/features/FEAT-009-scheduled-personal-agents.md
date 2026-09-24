# FEAT-009 — Scheduled personal and lab-operations agents

- **Status:** Partial (IWO-030 + IWO-052 timer live on mini; IWO-051 report format open)
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
| [IWO-052](../work-orders/IWO-052-scheduler-launchagent.md) | LaunchAgent / host timer | Minute tick on mini (`install-scheduler-launchagent.sh`) |

## Out of scope

Auto-restart hosts; auto `compose down -v`.

## Implementation status

| Layer | Status |
|-------|--------|
| Spec | Done |
| Code | Done for timer path — tick API + `com.ai-lab.scheduler-tick` plist + install script |
| Live | Mini LaunchAgent `com.ai-lab.scheduler-tick` installed 2026-09-24 |
