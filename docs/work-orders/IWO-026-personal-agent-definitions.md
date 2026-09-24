# IWO-026 — Personal agent deploy definitions

**Status:** Complete  
**Priority:** P1  
**Effort:** S  
**Feature:** [FEAT-013](../features/FEAT-013-personal-agent-studio.md), [FEAT-009](../features/FEAT-009-scheduled-personal-agents.md)  
**Risk tier:** P2

## Problem

No durable “personal agent” config beyond one-shot Run loop.

## What shipped

- `AgentDefinition` + SQLite store `~/.ai-lab/agent-definitions.sqlite`
- `GET/POST /v1/agent-definitions`, `POST .../runs` (bounded loop)
- Studio UI panel to create/list definitions
- Optional `schedule_cron` field stored (scheduler hook = FEAT-009 follow-on)

## Closeout

- Evidence: `tests.test_personal_agent_studio.AgentDefinitionStoreTests`
