# IWO-052 — Mini scheduler LaunchAgent (FEAT-009)

**Status:** Done  
**Priority:** P1  
**Effort:** S  
**Owner:** human (operator)  
**Feature:** [FEAT-009](../features/FEAT-009-scheduled-personal-agents.md)  
**Risk tier:** P1  

## Problem

IWO-030 exposes `POST /v1/scheduler/tick`, but nothing on the mini calls it on a
timer. Scheduled personal agents never fire unattended.

## Decision Context

- Chosen approach: user LaunchAgent `com.ai-lab.scheduler-tick` with
  `StartInterval` 60s calling `scripts/scheduler-tick.sh --apply`.
- Auto-detect Tailscale bind (mini API is not on loopback — ADR 0034).
- Install script dry-run by default; `--apply` bootstraps on this host.

## What To Build / Fix

- `hosts/m1-mini/com.ai-lab.scheduler-tick.plist.example`
- `scripts/install-scheduler-launchagent.sh` (dry-run / `--apply`)
- Improve `scheduler-tick.sh` host detection
- Docs: FEAT-009, mini RUNBOOK, IWO closeout
- Live apply on mini (operator Continue authorization)

## Out Of Scope

- System crontab
- Celery/Temporal
- Changing agent definition UI

## Acceptance Criteria

1. Dry-run prints paths without writing LaunchAgents. ✅
2. `--apply` on mini loads `com.ai-lab.scheduler-tick`. ✅
3. Manual tick still works; LaunchAgent log under `~/.ai-lab/`. ✅

## AI Lab gates

- **Host deploy / mutate authorized by this IWO alone?** Yes for mini timer —
  operator said Continue after scheduler was listed as next (2026-09-24).
- **May run on Air?** Install script dry-runs only; apply on mini.

## Closeout

- Verification evidence: mini `launchctl` showed agent loaded; kickstart + manual
  `./scripts/scheduler-tick.sh --apply` returned
  `{"ok":true,...,"started":[],"skipped":[],"errors":[]}`; log at
  `~/.ai-lab/scheduler-tick.log`.
- Host deploy performed? Yes — LaunchAgent installed for user `sgerhart` on
  mac-mini (2026-09-24). No agents due at that minute (empty started).
- Residual risk: StartInterval jobs exit between runs (`state = not running` is
  expected); watch log if tick returns non-JSON or auth errors.