# IWO-045 — DefenseClaw Cursor connector (Add)

**Status:** Complete  
**Priority:** P1  
**Effort:** S  
**Owner:** human (operator)  
**Feature:** [FEAT-014](../features/FEAT-014-defenseclaw-operator-governance.md)  
**Risk tier:** P1  

## Problem

DefenseClaw is live on the Air with Antigravity in action mode, but Cursor has
no hooks — this IDE session is ungoverened.

## What To Build / Fix

Authorized host mutate on Air:

```bash
defenseclaw setup cursor --mode action --human-approval --fail-mode open --yes --restart
```

Default is **Add** (keep Antigravity). Do not pass `--replace`.

## Out Of Scope

- Replacing Antigravity
- Mini gateway
- MCP allowlist changes

## Acceptance Criteria

1. `~/.cursor/hooks.json` present
2. `defenseclaw status` lists Cursor alongside Antigravity
3. Preflight reports cursor hooks present

## AI Lab gates

- **Host deploy / mutate authorized by this IWO alone?** Yes — operator asked
  to connect DefenseClaw to Cursor (2026-09-24)

## Closeout

- Verification evidence (2026-09-24 Air):
  - First apply fell back to observe (PATH `cursor` was not the IDE).
  - Retry with `/Applications/Cursor.app/.../bin` on PATH → `cursor mode=action`.
  - `~/.cursor/hooks.json` present; status: Antigravity + Cursor both RUNNING action.
- Follow-ons: IWO-046 scan lab MCP; ensure IDE `cursor` on PATH for future setups
- Host deploy performed? Yes (Air only; no mini)
