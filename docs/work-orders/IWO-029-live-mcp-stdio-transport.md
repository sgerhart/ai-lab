# IWO-029 — Live MCP stdio transport for Studio agents

**Status:** Complete  
**Priority:** P1  
**Effort:** M  
**Owner:** human (operator)  
**Feature:** [FEAT-013](../features/FEAT-013-personal-agent-studio.md)  
**Services / Areas:** platform (mcp_client, tool_runtime, agent_loop, control_app, Studio Settings)

## Problem

IWO-027 registers MCP servers under Settings and deny-by-default allowlisting, but
`call_mcp_tool` is a stub. Deployed agents cannot list or invoke real MCP tools.

## Decision Context

- Chosen approach: stdlib JSON-RPC over stdio with MCP Content-Length framing;
  short-lived process per list/call; tool names `mcp/<server_id>/<tool>`.
- Alternatives rejected: add full MCP SDK now (heavier dep); SSE/HTTP in this IWO.
- Assumptions: operator-configured `command` + `args` in `~/.ai-lab/mcp-servers.json`
  are trusted once listed; no `shell=True`.
- Open decisions: persistent MCP sessions / pooling (follow-on).

## What To Build / Fix

- Stdio MCP session: initialize → tools/list → tools/call
- `call_mcp_tool` / `list_mcp_tools` live for `transport=stdio`
- AgentRun carries `mcp_server_ids`; loop exposes MCP tools in the system prompt
- `GET /v1/mcp/servers/{id}/tools` for Settings verification
- Tests with a fake stdio MCP child process
- Docs: FEAT-013, IWO-027 note, index

## Expected Change Surface

- Expected: `mcp_client.py`, new helper as needed, `tool_runtime.py`, `agent_loop.py`,
  `conversation.py` (AgentRun field), `control_app.py`, `agents.html` note, tests
- Tests: `tests/test_personal_agent_studio.py` (or mcp transport tests)
- Docs/status: this IWO + FEAT-013 + index

## Out Of Scope

- SSE / HTTP MCP transports
- IDE → lab MCP server (FEAT-005)
- Repo allowlist population with real servers
- Host deploy / installing npm MCP packages on mini
- Persistent connection pool

## Do NOT Change

- Deny-by-default: unlisted servers still raise `McpDenied`
- No secrets or MCP tokens in Git
- No Docker socket MCP
- No host mutate from this IWO alone

## Acceptance Criteria

1. Fake stdio MCP server: list tools + call tool returns observation in unit tests
2. Unlisted server id still denied
3. Agent definition run with `mcp_server_ids` can invoke `mcp/<id>/<tool>` when listed
4. `GET /v1/mcp/status` reports `transport: stdio` (not stub-only)
5. `./scripts/validate-repo.sh` and unit tests for the new paths pass

## Validation Plan

- Automated: unittest discover for MCP transport + existing studio tests
- Manual (optional, operator): register a local stdio server on mini Settings, list tools
- Evidence: test output; status JSON `transport`

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** No
- **Privileged tools expected?** none by default; MCP tools inherit operator trust of the listed server
- **May run on Air?** Yes (unit tests)

## Closeout

- Evidence: `tests.test_personal_agent_studio.McpClientTests` (stdio list/call + tool_runtime route)
- Follow-ons: SSE/HTTP MCP; FEAT-009 schedules
