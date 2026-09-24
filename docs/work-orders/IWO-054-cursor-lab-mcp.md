# IWO-054 — Wire Cursor to lab MCP (FEAT-005)

**Status:** Done  
**Priority:** P1  
**Effort:** S  
**Owner:** human (operator)  
**Feature:** [FEAT-005](../features/FEAT-005-python-client-mcp.md)  
**Risk tier:** P1  

## Problem

IWO-042 shipped the stdio lab MCP server, but Cursor on the Air is not
configured to call the mini API. Operator next-step list includes this wire-up.

## Decision Context

- Use DefenseClaw `mcp set --connector cursor` so scan runs before trust
  (IWO-046 intent).
- Token via `~/.ai-lab/mac-mini-api.token` (script fallback); no token in
  mcp.json / Git.
- `AI_LAB_API_BASE=http://mac-mini:8088`

## What To Build / Fix

- `lab-mcp-server.sh` token fallback for Air (`mac-mini-api.token`)
- DefenseClaw Cursor MCP entry `ai-lab`
- Docs: FEAT-005 live, platform/mcp README, IWO closeout

## Out Of Scope

- Org-wide MCP rollout
- Privileged tools over MCP
- Publishing a PyPI client

## Acceptance Criteria

1. DefenseClaw scan does not block add (or finding recorded if it does).
2. Cursor MCP config lists `ai-lab` pointing at `scripts/lab-mcp-server.sh`.
3. Stdio smoke: `lab_health` succeeds against mini (no token in chat).

## AI Lab gates

- **Host deploy?** Air-local Cursor/DefenseClaw config only; operator Continue
  after MCP listed as next (2026-09-24).
- No secrets in Git.

## Closeout

- Verification evidence: Stdio `lab_health` against `http://mac-mini:8088`
  returned control-plane `ok` / `deployed=true`. Cursor `~/.cursor/mcp.json`
  lists `ai-lab` with script path + `AI_LAB_API_BASE` only (no token).
  DefenseClaw `mcp list --connector cursor` shows `ai-lab`.
- Host deploy performed? Air-local Cursor/DefenseClaw config only (2026-09-24).
  Scan skipped — see F-014 / IWO-046.
