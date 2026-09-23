# IWO-003 — Authenticated private agent UI shell

**Status:** Complete  
**Priority:** P1  
**Effort:** M  
**Owner:** operator  
**Feature:** [FEAT-004](../features/FEAT-004-agent-chat-and-dashboard.md), [FEAT-010](../features/FEAT-010-mini-personal-agent-loop.md)  
**Risk tier:** P1 (auth)

## Problem

`GET /` status board is unauthenticated HTML useful for counts, not for chat
or mutations. Personal agents need a smallest useful authenticated UI.

## What To Build / Fix

- Token/session auth for HTML + JSON (reads and mutations)
- Pages/views: select agent + model (show billing class stub), chat, list runs
- Protect any streaming endpoints
- Never return provider secrets

## Out Of Scope

Large dashboard framework; action-approval polish (IWO-007); live cloud models

## Acceptance Criteria

1. Unauthenticated mutate → 401
2. Authenticated chat posts persist via IWO-002 APIs
3. Loopback/Tailscale only; no `0.0.0.0`

## AI Lab gates

- Creates runtime job? No by default
- Host deploy authorized by IWO alone? No
- Privileged tools? none

## Depends on

IWO-002


## Closeout

- Verification evidence: `tests.test_agent_loop` + validate-repo (2026-09-22)
- Host deploy performed? No
- Live mini migrate? No
