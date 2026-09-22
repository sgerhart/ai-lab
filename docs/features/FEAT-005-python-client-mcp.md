# FEAT-005 — Python client and IDE MCP adapter

- **Status:** Specified
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
| IWO-020 | Python client package | Submit/fetch against test API |
| IWO-021 | Optional MCP server allowlist entry | Deny-unlisted still holds |

## Out of scope

Org-wide tokens; Clarion factory MCP.

## Implementation status

| Layer | Status |
|-------|--------|
| Spec | Done |
| Code | Not started (allowlist empty) |
| Live | No |
