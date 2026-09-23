# IWO-007 — Tool action-level approvals in UI and API

**Status:** Complete  
**Priority:** P0  
**Effort:** M  
**Owner:** operator  
**Feature:** [FEAT-004](../features/FEAT-004-agent-chat-and-dashboard.md), [FEAT-010](../features/FEAT-010-mini-personal-agent-loop.md)  
**Risk tier:** P0 (approval correctness)

## Problem

Approving a whole work order is not the same as approving one tool call.
Humans must see arguments and deny without the action executing.

## What To Build / Fix

- Pause on gated tool with args snapshot
- UI approve/deny specific action
- Audit trail; distinguish from IWO/plan approval

## Acceptance Criteria

1. Unapproved gated tool does not execute
2. Deny leaves run recoverable/failed visibly
3. Args visible before decision

## Depends on

IWO-003, IWO-005; ADR 0018


## Closeout

- Verification evidence: `tests.test_agent_loop` + validate-repo (2026-09-22)
- Host deploy performed? No
- Live mini migrate? No
