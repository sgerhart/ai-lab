# FEAT-013 — Personal Agent Studio (chat, agents, MCP, attachments)

- **Status:** Partial (shell live — chat, attachments, in-app settings, model picker. Agent create/run layout is open: D-019)
- **Created:** 2026-09-23
- **Owner:** human (operator)
- **Priority:** Core product surface (extends FEAT-004 / 010 / 011)

## Purpose

Evolve the mini UI into a **Personal Agent Studio** at `/`: a
ChatGPT / Cursor-like conversation UI on the mini where the operator can chat,
attach documents and images, run or deploy personal agents, and (later) connect
allowlisted MCP servers—while **Studio Ollama remains the default LLM** and
usage-billed frontier models are reserved for explicit modes (e.g. deep
research).

## Product principles

1. **Studio-first.** Default chat and most agent loops use Studio local models
   (billing class `local`). No silent switch to paid APIs (ADR 0038).
2. **Frontier is opt-in.** Deep research / heavy synthesis may call an authorized
   foundational model only when the operator selects that mode and
   `usage_billed_authorized` + keys are set (IWO-021).
3. **Chat ≠ deploy.** Ordinary turns stay conversation-scoped. Deploying a
   personal agent creates a durable definition + schedule/run policy (FEAT-009).
4. **MCP is deny-by-default.** Agents may only use MCP servers on an explicit
   allowlist (extends `platform/mcp/allowlist.json`). FEAT-005 (IDE → lab MCP)
   remains a separate direction.
5. **Attachments stay off Git.** Files land under `~/.ai-lab/` (or object store
   later); metadata in Postgres; never committed.

## User workflow (target)

1. Open Personal Agent Studio over Tailscale at `/` (`/agents` and `/lab` redirect here).
2. Pick or create a conversation; optional agent persona.
3. Chat with Studio model; stream tokens; attach PDF/Markdown/images.
4. Toggle **Deep research** when a frontier pass is warranted (visible
   `usage_billed_api` pill + confirm).
5. From a thread or template: **Deploy personal agent** (name, tools/MCP,
   schedule or on-demand, approval policy).
6. Inspect runs, approvals, artifacts; cancel/retry safely.

## Target host(s)

| Role | Host | Why |
|------|------|-----|
| UI + API + agent SoT | `mac-mini` | Always-on control plane |
| Default inference | `mac-studio` | Ollama / MLX |
| Frontier (opt-in) | cloud via mini egress | IWO-021 adapters |
| Browser | `mac-air` | Human plane |

## Dependencies

- FEAT-004 (UI), FEAT-010 (loop), FEAT-011 (router), FEAT-012 (secrets)
- FEAT-008 (retrieval) for research citations later
- FEAT-009 (scheduled agents) for deploy/schedule
- ADR 0034, 0037, 0038; MCP deny-by-default

## Distinct from

| Existing | Relation |
|----------|----------|
| FEAT-004 | This Feature **absorbs** the ChatGPT-class UX upgrade |
| FEAT-005 | Lab as MCP *server* for IDEs — different from agents as MCP *clients* |
| FEAT-007 | Coding/PR factory — optional later, not the Studio chat core |
| FEAT-008 | Retrieval/memory backend consumed by deep research |

## Proposed implementation work orders

| ID | Title | Depends on | Acceptance (sketch) |
|----|-------|------------|---------------------|
| [IWO-024](../work-orders/IWO-024-personal-agent-studio-shell.md) | ChatGPT/Cursor-like shell + streaming | FEAT-004 live | Sidebar + stream + Studio default |
| [IWO-025](../work-orders/IWO-025-conversation-attachments.md) | Attachments (docs/images) | IWO-024 | Upload → store → model/context |
| [IWO-026](../work-orders/IWO-026-personal-agent-definitions.md) | Personal agent deploy definitions | IWO-024, FEAT-009 | Create/list/run durable agent configs |
| [IWO-027](../work-orders/IWO-027-mcp-client-allowlist.md) | MCP client allowlist for agents | IWO-026 | Only listed servers; deny-unlisted |
| [IWO-028](../work-orders/IWO-028-deep-research-mode.md) | Deep research mode (Studio + frontier) | IWO-021 | Explicit mode; billing visible |
| [IWO-029](../work-orders/IWO-029-live-mcp-stdio-transport.md) | Live MCP stdio transport | IWO-027 | List/call tools; agent `mcp/<id>/<tool>` |

## Acceptance criteria (Feature-level)

- [x] Operator chats in a modern thread UI with Studio as default
- [x] Can attach documents/images used in a turn (with size/type limits)
- [x] Can define and run a personal agent beyond one-shot “Run loop”
- [x] Agents and Runs are full main-pane views (not drawers); Lab / API keys / Help live under Operator → Settings
- [x] Chats can be deleted from the sidebar
- [x] MCP only via allowlist + local `~/.ai-lab/mcp-servers.json`; unlisted refused; Settings has connect UI
- [x] Stdio MCP list/call live (IWO-029); SSE/HTTP still out of scope
- [x] Deep research uses frontier only when selected + authorized
- [x] No secrets or attachment bytes in Git
- [x] Operator menus stay inside Studio. Status Dashboard and New chat stay fixed. Under the line, Jupyter Labs, Agent Studio, MCP, Security, Configure, Projects, and Chats scroll together. Search is the magnifying glass beside AI LAB. The old `/lab` hub is retired
- [x] Chat model list comes from installed Studio Ollama tags
- [ ] Agent create/run layout accepted by the operator (D-019)

## Out of scope

- Public Internet SaaS; scraping ChatGPT/Claude UIs
- Unrestricted web crawl without a research IWO
- Replacing Clarion / factory products inside this repo
- Auto-enabling paid APIs
- SSE / HTTP MCP transports (stdio only in IWO-029)

## Implementation status (honest)

| Layer | Status | Evidence |
|-------|--------|----------|
| Spec | Done | this file |
| Code | Partial | IWO-024–029 and IWO-059 in Git. Studio is `/`. SSE/HTTP MCP not wired |
| Deploy | Partial | live on mini after operator sync |
| Live verified | Partial | Studio chat and settings used 2026-09-25. Agent and project screens still need refinement |
