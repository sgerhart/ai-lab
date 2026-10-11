# Implementation Work Order: IWO-103 — Conversational Scheduling and Durable Memory

**Title:** Conversational Scheduling and Durable Second Brain Memory Writing
**Status:** Completed
**Assigned to:** Pair / Agent
**Date:** 2026-10-11
**Related Documents:**
- `docs/features/FEAT-009-scheduled-personal-agents.md`
- `docs/features/FEAT-008-research-retrieval-memory.md`
- `docs/work-orders/IWO-102-modern-agent-harness-and-second-brain.md`
- `AGENTS.md`

---

## 1. Objective

Equip the Second Brain / Personal Agent with conversational capabilities to:
1. Schedule and manage recurring background cron runs directly in natural language (`schedule_create`, `schedule_list`, `schedule_cancel`).
2. Proactively record durable insights, preferences, decisions, and project facts into the personal memory vault (`vault_write`).

---

## 2. Requirements

1. **Scheduling Tools**:
   - `schedule_create`: Validate 5-field cron expression, create or update `AgentDefinition` in `AgentDefinitionStore`, link to daemon scheduler.
   - `schedule_list`: Query active recurring definitions and return cron schedules.
   - `schedule_cancel`: Remove or clear cron schedule for a given definition by ID or title.
2. **Memory Writing Tool**:
   - `vault_write`: Safely record markdown documents with YAML frontmatter in `~/.ai-lab/memory/knowledge/{category}/{slug}.md` (`preferences`, `facts`, `decisions`, `projects`, `people`).
3. **Policy & Prompt Integration**:
   - Add `schedule_create`, `schedule_list`, `schedule_cancel`, `vault_write` to `agents/personal/policy.json`.
   - Update agent loop prompt guidance to teach the model how to parse natural language schedules into 5-field cron strings (`0 9 * * 1`) and when to store memory insights.
4. **Safety & Confinement**:
   - No filesystem escape outside vault.
   - Strict 5-field cron syntax validation via `parse_cron`.

---

## 3. Validation

- Unit tests verifying `schedule_create`, `schedule_list`, `schedule_cancel`, and `vault_write`.
- All repository validation and structure tests pass.
- Verified on local host and deployed to Mac mini control plane daemon.
