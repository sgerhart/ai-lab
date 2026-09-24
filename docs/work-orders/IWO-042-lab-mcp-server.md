# IWO-042 — Lab MCP server for IDEs (FEAT-005)

**Status:** Complete  
**Priority:** P1  
**Effort:** M  
**Owner:** human (operator)  
**Feature:** [FEAT-005](../features/FEAT-005-python-client-mcp.md)  
**Services / Areas:** platform (lab_mcp_server, client), scripts, docs  
**Risk tier:** P2  
**GitHub:** [#6](https://github.com/sgerhart/ai-lab/issues/6)

## Problem

IDEs (Cursor) cannot call the mini control plane via MCP. FEAT-005 needs a
deny-by-default *lab-as-server* path (distinct from agents as MCP *clients*).

## Decision Context

- Chosen approach: stdio MCP server (`python -m ai_lab_platform.lab_mcp_server`)
  that proxies a small allowlisted tool set to the control-plane HTTP API using
  `AI_LAB_API_TOKEN` + `AI_LAB_API_BASE` (default `http://127.0.0.1:8088`).
  Thin `LabApiClient` shared helper for scripts.
- Alternatives rejected: SSE/HTTP MCP transport in this IWO; exposing all API
  routes as tools.
- Assumptions: operator configures Cursor MCP locally; no org-wide tokens.
- Open decisions: packaging as a published PyPI client (later).

## What To Build / Fix

- `lab_mcp_server.py` — initialize / tools/list / tools/call
- Tools: `lab_health`, `lab_memory_search`, `lab_memory_upsert`, `lab_scheduler_status`
- `LabApiClient` HTTP helper
- `scripts/lab-mcp-server.sh`
- Docs: Cursor mcp.json example; FEAT-005; #6
- Unit tests (in-process handlers + stdio smoke)

## Out Of Scope

- Installing Cursor config on any host
- Agent client allowlist changes (FEAT-013)
- Privileged deploy/git tools over MCP

## Do NOT Change

- Deny-by-default agent MCP client policy
- Secrets in Git; `0.0.0.0` binds

## Acceptance Criteria

1. Stdio server lists tools and answers `lab_health` in tests.
2. `lab_memory_search` / upsert round-trip against TestClient-backed API.
3. Docs show how to wire Cursor without committing tokens.

## AI Lab gates

- **Creates runtime job on mac-mini?** No
- **Host deploy authorized by this IWO alone?** **No**
- **May run on Air?** Yes (unit + local MCP against mini over Tailscale)

## Closeout

- Verification evidence: `python3 -m unittest tests.test_lab_mcp_server -v`
- Follow-ons: IWO-043 richer Python client; more IDE tools (conversations/runs)
- Docs/status updated: FEAT-005, `platform/mcp/README.md`
- Host deploy performed? No
