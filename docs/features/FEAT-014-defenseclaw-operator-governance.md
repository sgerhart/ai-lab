# FEAT-014 — DefenseClaw operator governance (Air)

- **Status:** Specified (partial live — DefenseClaw already on Air)
- **Created:** 2026-09-24
- **Owner:** human (operator)
- **GitHub issue:** draft only

## Purpose

Keep Cisco DefenseClaw as the **Air operator-plane** governance layer for IDE
hooks, MCP/skill scanning, and audit — adjacent to `ai-lab`, not absorbed into
mini compose (ADR 0025). Wire Cursor (and later lab MCP) under explicit
authorization so personal-agent and Studio workflows inherit inspection without
moving secrets or the gateway onto the mini.

## User workflow

1. DefenseClaw stays installed on the Air (`~/.defenseclaw`).
2. Operator runs lab preflight (`scripts/defenseclaw-preflight.sh`) — read-only.
3. When authorized: add Cursor connector **without replacing** Antigravity
   (`defenseclaw setup cursor` → Add).
4. Optionally scan `scripts/lab-mcp-server.sh` / MCP config before trusting it.
5. Audit evidence stays under `~/.defenseclaw/audit.db` (never Git).

## Target host(s)

| Role | Host alias | Why |
|------|------------|-----|
| DefenseClaw CLI + gateway | `mac-air` | Operator IDE plane |
| Lab API / Studio | `mac-mini` / `mac-studio` | Unchanged; governed only via Air clients |

## Dependencies

- FEAT-005 (lab MCP), FEAT-013 (Studio)
- ADR 0025 (adjacent product stacks)
- Live: DefenseClaw 0.8.x on Air (observed 2026-09-24)

## Proposed deliverables

- Inventory + this Feature
- Read-only preflight script
- IWOs for Cursor connector (deploy-gated) and optional lab-MCP scan

## Proposed implementation work orders

| ID | Title | Depends on | Acceptance |
|----|-------|------------|------------|
| [IWO-044](../work-orders/IWO-044-defenseclaw-preflight.md) | Preflight + docs | — | Script reports status; no host mutate |
| IWO-045 | Cursor connector (Add) | IWO-044 | Hooks present; Antigravity kept — **deploy auth** |
| IWO-046 | Scan lab MCP before Cursor trust | IWO-045 | Finding recorded; allow/block policy explicit |

## Acceptance criteria

- [x] Inventory records DefenseClaw on Air without secrets
- [x] Preflight is dry-run / read-only by default
- [ ] Cursor connector only after separate human authorization
- [ ] No DefenseClaw gateway on mini without a new ADR

## Out of scope

- Absorbing DefenseClaw into lab compose
- Committing `config.yaml`, `device.key`, or audit DB
- Replacing Antigravity with Cursor (must Add)

## Implementation status (honest)

| Layer | Status | Evidence |
|-------|--------|----------|
| Spec | Done | this file |
| Code | Partial | IWO-044 preflight |
| Deploy | No Cursor hooks yet | observed |
| Live verified | Partial | CLI/gateway 0.8.10 on Air |
