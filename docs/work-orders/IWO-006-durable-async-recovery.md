# IWO-006 — Durable async recovery, cancel, and safe retry

**Status:** Draft  
**Priority:** P1  
**Effort:** M  
**Owner:** operator  
**Feature:** [FEAT-002](../features/FEAT-002-durable-background-execution.md), [FEAT-010](../features/FEAT-010-mini-personal-agent-loop.md)  
**Risk tier:** P1

## Problem

Need explicit recovery for agent runs: Air closed, process restart, provider
down—runs must remain retrievable or fail visibly. Cancel and retry must be safe.

## What To Build / Fix

- Reconcile stuck `running`; cancel semantics; retry only when safe
- Link background runs to conversations
- Tests for restart + provider-unavailable

## Depends on

IWO-005
