# FEAT-004 — Interactive agent chat UI and work-order dashboard

- **Status:** Partial (Personal Agent Studio shell)
- **Created:** 2026-09-21
- **Owner:** human (operator)
- **GitHub issue:** [#5](https://github.com/sgerhart/ai-lab/issues/5)

## Purpose

Private, authenticated UI on the mini for **conversational chat** with personal
agents and for inspecting durable runs—smallest useful surface first, not a
large dashboard framework.

## User workflow

1. Open mini UI over loopback/Tailscale (Air browser or phone later).
2. Authenticate (token/session); all reads and mutations require auth.
3. Select agent + model (see billing class: local / subscription_client /
   usage_billed_api — ADR 0038).
4. Chat ordinarily **or** start/monitor a background runtime work order.
5. See live/queued/awaiting_approval/blocked/failed/complete.
6. Inspect tool actions, observations, artifacts; approve/deny a **specific
   proposed action** with arguments visible.
7. View provider health and usage/cost estimates; cancel; retry only when safe.

## Distinctions (required)

| Concept | Meaning |
|---------|---------|
| Ordinary chat turn | May be ephemeral or conversation-scoped; **not** every turn is a gated job |
| Durable runtime WO / agent run | Background; survives Air sleep |
| Approve tool action | Gate on one tool call + args |
| Approve implementation plan | FEAT-001 / IWO review — different workflow |

## Target host(s)

| Role | Host alias | Why |
|------|------------|-----|
| UI + API | `mac-mini` | Private status board extension |
| Browser | `mac-air` (or phone on tailnet) | Human plane |

## Dependencies

- FEAT-010, FEAT-011, FEAT-002; ADR 0034, 0038

## Proposed deliverables

- Auth for HTML + API + streaming
- Chat view + run detail + approval panel
- Provider status strip
- Redaction; no secrets to browser
- Extend existing `status.html` rather than a new SPA framework initially

## Proposed implementation work orders

| ID | Title | Depends on | Acceptance |
|----|-------|------------|------------|
| IWO-003 | Authenticated agent UI shell | IWO-002 | Chat + status with token |
| IWO-007 | Action-level approvals in UI | IWO-003, IWO-005 | Deny stops run |

## Acceptance criteria

- [x] Authenticated chat with agent + model select
- [x] Run states visible; approve/deny specific action
- [x] Billing class visible; secrets not exposed
- [x] Streaming endpoints protected
- [ ] Mobile-on-tailnet acceptable later (not blocking)

## Out of scope

- Public Internet exposure; large dashboard framework before chat works

## Implementation status (honest)

| Layer | Status | Evidence |
|-------|--------|----------|
| Spec | Done | this file |
| Code | Partial | Personal Agent Studio `/agents` (sidebar, stream, attach, deploy) |
| Deploy | Partial | live on mini:8088 |
| Live verified | Partial | pre-Studio shell verified; Studio shell pending deploy |
