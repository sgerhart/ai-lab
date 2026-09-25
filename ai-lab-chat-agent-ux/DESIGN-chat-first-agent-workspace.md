# AI Lab — Chat-First Agent Workspace

**Status:** Proposed design · **Date:** 2026-09-24 · **Scope:** AI Lab user experience and mini-side agent integration

## 1. Decision and purpose

**Chat is the primary product surface.** A user should open AI Lab, converse with one assistant, inspect available capabilities, delegate a bounded task, approve sensitive actions, and retrieve results later in the same conversation. “Agent definitions,” model configuration, MCP server management, run traces, and schedules are secondary controls, not mandatory prerequisites to chatting.

The user has a usable chat and a Jupyter launch path today, but does not like the separate Agents experience. Preserve what works; consolidate the experience instead of building a new framework or second app.

### Non-goals

- Replacing Cursor or moving Clarion into AI Lab.
- A new model router, MCP transport, scheduler, or Work Order protocol.
- Automatic model pulls, host provisioning, API spending, or unrestricted repository/shell tools.
- Promising recovery across mini process restarts before it has been verified.
- Making every chat message a durable agent job.

## 2. Architecture and execution contract

```text
Browser on Air / Studio / other tailnet device
   ↕ chat, capability catalog, progress, approval, results
Mac mini — FastAPI + conversation/run store + orchestrator + MCP client
   ├─ local/built-in tools executed on mini (within their actual policy)
   ├─ stdio MCP servers launched on mini, if configured
   ├─ remote MCP servers executed at their actual remote host
   ├─ queued background agent runs owned by mini worker
   └─ model requests → Mac Studio Ollama (or explicitly authorized API)
Mac Studio — Ollama, Jupyter, Antares, compute services
Mac Air — browser, Cursor/IDE, human review, separate product repos
```

A browser tab is never the execution owner for a delegated task. A mini-side queued run may continue when the Air closes. Do not claim crash/restart recovery until tests demonstrate it. An interactive chat response and a delegated background run are distinct modes with a consistent conversation presentation.

## 3. Information architecture

**Primary navigation:** Chat · Jupyter · Activity. **Secondary settings:** Capabilities · Models · Agent presets · Schedules · Security/approvals · Diagnostics. Reuse existing routes/components where practical; avoid a big-bang replacement of `web/agents.html`.

### Chat header

- Assistant identity: “AI Lab Assistant” by default; optional preset switch for specialized behavior.
- Active model: actual backend/model and local versus usage-billed status.
- Mini/Studio health: connected, degraded, unavailable, last checked; never infer health from configuration alone.
- Compact capability badges for enabled tools and MCP servers; overflow into “Capabilities”.
- Prominent “Open Jupyter” action, retaining existing Studio launch flow and auth handling.

### Composer

One input for questions and delegated tasks. Attachments, model choice, and capabilities are optional controls. A task can be delegated explicitly (“Run in background”) or via a clearly explained confirmation; never silently convert a normal chat message into an unattended privileged job. A new user should not need to create an agent definition.

### Conversation timeline

Represent user and assistant messages, tool-use events, approval requests, and background-run cards in chronological order. Collapse technical traces by default. A run card displays objective, status, start/update time, model/provider, tools used, result/error, and “View details.” It remains attached to its conversation after reconnect. A background run must not overwrite unrelated chat messages.

## 4. Capability badge system

Badges represent **capabilities available to this conversation**, not generic installed integrations. Types: `built_in`, `custom_mcp`, `third_party_mcp`, `remote_mcp` (hosting location is a separate field), and `provider` where appropriate. MCP source/ownership and execution host are separate dimensions.

Badge states: `configured`, `connecting`, `connected`, `degraded`, `unavailable`, `disabled`, `permission_required`, `unknown`. Only label a capability “connected” after a recent successful handshake or health check. Include `last_checked_at`; stale state becomes `unknown` or “last seen,” not green.

Badge detail panel: display name, source/publisher as configured, transport, **where the server runs**, actual connection state, last check, exposed tool names and descriptions, per-conversation enablement, read/write/privileged classification, and required approvals. Never display tokens, secrets, raw connection URLs containing credentials, or sensitive environment values. Third-party metadata is untrusted display text; render as text, not HTML.

During a run, show **used** badges inline with action summaries (“GitHub · read repository”), outcomes, and approval state. Distinguish “available” from “used.” Do not show a server badge as if all its tools are authorized merely because its connection works.

## 5. Agent semantics

The default assistant is an existing agent definition/preset chosen automatically or via configuration. A preset defines instructions and allowed capabilities, not a separate user-facing chat application. The operator can switch preset or model with an explicit indication of the scope (current conversation vs next run). Persist effective model, preset, allowed server/tool IDs, and billing class per run for audit.

The mini validates permissions before executing tools. The model cannot grant itself tools or widen a workspace. MCP tools need tool-level authorization and risk classification, even when their server is enabled. Privileged or side-effecting calls require exact-action approval (server, tool, canonical arguments, target, expiry, run/action ID); denial is visible in the conversation. A connection badge is not an approval grant.

## 6. Background execution and reconnect

`queued → running → awaiting_approval → completed | failed | cancelled` is the primary run lifecycle. The browser submits a task once and receives a run ID; UI updates by polling existing endpoints initially, with streaming only if it fits existing architecture. The mini owns execution. Reopening the same conversation reconstructs messages, active run cards, approvals, and completed results from durable storage. Include safe retry/idempotency semantics to avoid duplicate runs on browser reconnect.

Before promising reliable unattended execution, verify worker enablement on live mini, queue claim behavior, restart recovery, side-effect replay prevention, and enforcement of step/time/token/cost budgets. For V1, label restart recovery “not yet verified” if that is the true state.

## 7. Jupyter

Retain a one-click Studio Jupyter launch in the header and/or lab navigation. Show Studio connectivity and a truthful unavailable state. Avoid putting bearer/Jupyter tokens into UI logs, analytics, or copyable status fields; review existing token-bearing launch URL and browser-history exposure as part of security hardening. Notebook execution is Studio-side, not mini-side.

## 8. Security, accessibility, and responsive UX

- Preserve fail-closed authentication; verify live deployment and rotate exposed credentials (F-012/F-013).
- No silent local-to-paid fallback; require explicit paid API authorization.
- Escape all user, tool, MCP, model, and repo-derived strings before DOM insertion. Prefer `textContent` over interpolated `innerHTML`.
- Keyboard-operable composer, badges, approval dialog; visible focus, status text beyond color, responsive narrow-screen layout.
- Never expose tool arguments containing secrets in badges, timeline, or audit exports; redact consistently.
- Keep diagnostics accessible without making raw traces the default UX.

## 9. Existing implementation to reuse / verify

At reviewed `main` `ef48d50`: chat and Jupyter launch exist; `GET /v1/models` exposes model profiles and Studio Ollama choices (IWO-055 complete); agent definitions, conversations/runs, background worker, scheduler, MCP stdio client and settings UI exist. Qwen models are catalogued, not pulled. Do not rebuild those layers. Verify live mini/Studio behavior independently of docs and unit tests. Relevant starting points: `platform/src/ai_lab_platform/control_app.py`, `agent_worker.py`, `agent_loop.py`, `mcp_stdio.py`, `tool_runtime.py`, `web/agents.html`, `models/catalog.json`, FEAT-013, FEAT-016, F-012/F-013.

## 10. Phased release and acceptance

**V1:** Default assistant in chat, model/status header, truthful capability badges, tool-use timeline, read-only MCP/lab-health task queued on mini, reopen same conversation on Air, Jupyter launch preserved. No write-capable coding agent.

**V1.1:** Capability details and per-conversation enablement, exact-action approvals in chat, scheduler/activity discoverability, stronger worker recovery and budget enforcement.

**V2:** Read-only Coding Assistant on fixture repository (IWO-056) and model evaluation (IWO-057). Isolated write path only after hardening gates; no live Clarion first test.

### End-to-end usability test

From Air, open chat without creating an agent definition. Ask: “Check AI Lab health using your available tools and summarize what needs attention.” See available badges and actual used-tool events. Delegate as a background run, close the Air, reopen from another browser, see the same conversation and result. Open Studio Jupyter. Repeat with unavailable MCP and Studio offline; show truthful degraded states and no paid fallback. Test denial of unauthorized write/tool calls.

## 11. Success metrics

Time from first visit to useful chat; percentage of tasks requiring Agents-settings navigation; truthful connection-state rate; task retrieval after browser disconnect; duplicate-run rate; approval clarity; operator acceptance of timeline density. Collect no secret values or unnecessary prompt content in telemetry.

## 12. Open decisions for owner

- Whether “Activity” is a separate top-level nav item or a chat sidebar.
- Default preset identity/name and whether model selection persists per conversation.
- Whether a third-party MCP is opt-in per conversation or inherits a safe default allowlist.
- Live deployment acceptance criteria for crash/restart recovery (required before calling it guaranteed).
