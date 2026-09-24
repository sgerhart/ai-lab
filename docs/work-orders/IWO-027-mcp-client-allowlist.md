# IWO-027 — MCP client allowlist for agents

**Status:** Complete (stub transport)  
**Priority:** P1  
**Effort:** S  
**Feature:** [FEAT-013](../features/FEAT-013-personal-agent-studio.md)  
**Risk tier:** P1

## Problem

Personal agents need a path to MCP servers without opening deny-by-default.

## What shipped

- `mcp_client.py`: status + `require_mcp_servers` / `call_mcp_tool`
- `GET /v1/mcp/status`
- Agent definitions reject unlisted `mcp_server_ids`
- Allowlist remains empty; unlisted denied

## Out Of Scope

Live MCP JSON-RPC transport until an operator-approved allowlist entry + ADR

## Closeout

- Evidence: `tests.test_personal_agent_studio.McpClientTests`
