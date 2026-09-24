# IWO-024 — Personal Agent Studio chat shell (streaming)

**Status:** Complete  
**Priority:** P1  
**Effort:** M  
**Owner:** operator  
**Feature:** [FEAT-013](../features/FEAT-013-personal-agent-studio.md), [FEAT-004](../features/FEAT-004-agent-chat-and-dashboard.md)  
**Risk tier:** P2  
**Services / Areas:** platform (web + API)

## Problem

`/agents` felt like a lab panel: no conversation list, no streaming, weak product framing.

## What shipped

- Sidebar conversation list via `GET /v1/conversations`
- SSE `POST .../messages/stream` (Ollama stream; other backends one-shot chunk)
- ChatGPT-like shell: toolbar, thread, composer
- Studio Ollama default when healthy

## Closeout

- Evidence: store list tests; UI on `/agents`; SSE event shape
  `user` / `token` / `done` / `error`
- Follow-ons completed in same Feature batch: IWO-025–028
