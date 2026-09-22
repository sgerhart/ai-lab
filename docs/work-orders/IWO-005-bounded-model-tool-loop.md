# IWO-005 — Bounded LangGraph model/tool loop (lab-operations)

**Status:** Draft  
**Priority:** P1  
**Effort:** L  
**Owner:** operator  
**Feature:** [FEAT-010](../features/FEAT-010-mini-personal-agent-loop.md)  
**Risk tier:** P1

## Problem

Deterministic `agent_plans.py` is not a model-driven loop. Need a finite
LangGraph loop on the mini: model → validate tool → execute or approve →
observe → repeat under budgets.

## What To Build / Fix

- Graph nodes for FEAT-010 loop steps
- Start with read-only `lab-operations` tools only
- Budgets: max steps / time / tokens
- Tests: ≥2 model/tool steps with FakeBackend; denial path; interrupt path

## Out Of Scope

New write/privileged tools; Studio requirement; coding agent

## Acceptance Criteria

1. FakeBackend run shows ≥2 tool observations
2. Disallowed tool never executes
3. Budget exhaustion stops cleanly
4. `agent_plans.py` remains available as fixture

## Depends on

IWO-002, IWO-004
