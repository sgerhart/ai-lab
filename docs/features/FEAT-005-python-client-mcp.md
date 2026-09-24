# FEAT-005 — Python client and IDE MCP adapter

- **Status:** Partial (IWO-042 lab MCP server in Git)
- **Created:** 2026-09-21
- **Owner:** human (operator)
- **GitHub issue:** [#6](https://github.com/sgerhart/ai-lab/issues/6)

## Purpose

Call the mini API from scripts and IDE agents under deny-by-default MCP—after
the private UI chat path works (FEAT-004/010).

## User workflow

Install client or enable listed MCP server → submit/list/approve/chat against
loopback or Tailscale; unlisted MCP refused.

## Dependencies

FEAT-002, FEAT-010; new ADR if enabling first MCP server.

## Proposed IWOs

| ID | Title | Acceptance |
|----|-------|------------|
| [IWO-042](../work-orders/IWO-042-lab-mcp-server.md) | Lab stdio MCP server + LabApiClient | IDE tools hit mini API |
| IWO-043 | Richer Python client (submit/approve/chat) | Scripted WO lifecycle |

Note: IWO-020/021/022/023 numbering collided with other tracks; IWO-042 supersedes
the old IWO-022/023 titles for the MCP server slice.

## Out of scope

Org-wide tokens; Clarion factory MCP.

## Implementation status

| Layer | Status |
|-------|--------|
| Spec | Done |
| Code | Partial — `lab_mcp_server` + `LabApiClient` (IWO-042) |
| Live | Operator wires Cursor locally; not auto-installed |
