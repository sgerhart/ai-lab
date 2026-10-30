# IWO-114 — Steward Conversational Chief of Staff Desk Redesign

**Status:** Complete (unit; not deployed)  
**Priority:** P1  
**Effort:** M  
**Owner:** human / Antigravity  
**Feature:** FEAT-004, FEAT-022  
**Services / Areas:** platform, docs  

Work Order Protocol Level 2 implementation order for transforming the Steward interface into an executive Chief of Staff interactive desk with natural language conversational companion, 1-click preset templates, elevated watch cards, and a chronological intelligence feed.

## Problem

The current Steward interface on `http://mac-mini:8088/` (both in `agents.html#steward` and `steward.html`) has significant visual and interaction shortcomings:
1. **Broken Accessibility Tokens:** Missing `.visually-hidden` styling in `steward.css` and `agents.html` caused screen-reader accessibility labels and raw `<select id="wake-preset">` elements to render directly on screen, creating duplicated text ("What it should look after" followed by placeholder "What should it look after?") and an unstyled dropdown in the middle of rhythm buttons.
2. **Cold Database Form UX:** The user is immediately greeted by a rigid cron form and a wall of 8 glowing tool buttons, creating the impression of a database configuration page rather than an intelligent companion.
3. **No Conversational Interface:** Despite Steward being the personal autonomous Chief of Staff backed by Ollama, the user cannot interact conversationally on the web desk to brainstorm, ask questions, review findings, or assign responsibilities in natural language.
4. **Unstructured Findings:** Notes brought back by wakes are crammed into a secondary column without rich markdown formatting, timestamps, or quick-action triggers.

## Decision Context

- **Conversational Chief of Staff Desk Architecture:** Adopt a unified three-tab executive desk under the living presence header:
  1. `💬 Chief of Staff Conversation`: Interactive dialog with Steward backed by the personal agent loop (`Conversation.new(agent="personal")`), zero-state curated starter cards, and live agent reasoning status.
  2. `🛡️ Standing Watches`: Executive card deck featuring 1-click Quick Templates (*Morning Briefing*, *Research Sentinel*, *Lab Pulse*, *Vault Journal*), elevated cards with live pulsing status indicators and countdowns, and a clean, collapsible "New Watch" composer with categorized tool drawers.
  3. `📋 Intelligence Feed`: Full-width timeline of findings brought back by background wakes with markdown formatting, source tool chips, and *Run Wake Now* shortcuts.
- **Visual Excellence & Polish:** Fix `.visually-hidden`, apply glassmorphic dark-mode aesthetics (`Outfit` and `Inter` typography, glowing cyan/azure/indigo accents, smooth transitions), and eliminate cluttered pill walls.
- **Safety Boundaries:** Background wakes remain strictly within the **See** ceiling; mutations remain gated behind human approvals (ADR 0018, FEAT-022).
- **Host Deployment Gate:** Code is developed and tested in Git; live host deployment to `mac-mini` is deferred until explicitly authorized by the operator.

## What To Build / Fix

1. **Accessibility & Utility Tokens (`steward.css`, `agents.html`):**
   - Implement `.visually-hidden` with standard zero-size clipping to hide accessibility labels and native fallback `<select>` elements.
2. **Tabbed Executive Desk Navigation (`agents.html`, `steward.html`, `steward.css`):**
   - Add glassmorphic tab switcher: `[💬 Conversation]`, `[🛡️ Standing Watches (N)]`, `[📋 Intelligence Feed]`.
3. **Conversational Desk View (`steward.js`, `steward.css`):**
   - Connect to `/v1/conversations` (filtering or creating `agent: "personal"`).
   - Render chat messages with safe HTML/markdown formatting.
   - Zero-state prompt starter cards with 1-click fill/send.
   - Floating glass composer with auto-resize textarea and send button.
   - Thinking indicator showing active tool execution during personal agent runs.
4. **Standing Watches Executive Deck (`steward.js`, `steward.css`):**
   - 1-click Quick Templates row.
   - Refined watch cards with status badge (Active, Paused, Closed), rhythm chip, tools tags, and action buttons (*⚡ Wake now*, *⏸ Pause / ▶ Resume*, *✕ Close*).
   - Clean, collapsible watch creator with rhythm buttons and categorized tool drawer.
5. **Intelligence Feed View (`steward.js`, `steward.css`):**
   - Formatted chronological timeline of wake findings with source tags and wake re-trigger.
6. **Validation:**
   - Run repo validation (`./scripts/validate-repo.sh`, `./tests/test_structure.sh`).
   - Run platform test suite (`python3 -m unittest discover -s tests -v`).

## Expected Change Surface

- `platform/src/ai_lab_platform/web/static/steward.css`
- `platform/src/ai_lab_platform/web/static/steward.js`
- `platform/src/ai_lab_platform/web/agents.html`
- `platform/src/ai_lab_platform/web/steward.html`
- `docs/work-orders/IWO-114-steward-conversational-chief-of-staff-desk.md`
- `docs/work-orders/README.md`

## Out Of Scope

- Modifying host launchd plists on `mac-mini`.
- Changing the backend permissions model or agent execution pipeline.

## Do NOT Change

- Binds stay `127.0.0.1` or Tailscale IPv4; never `0.0.0.0`.
- Three-class security model (ADR 0018, FEAT-022) with read-only background wakes.
- Git author: `Steven Gerhart <sgerhart@gmail.com>`.

## Acceptance Criteria

1. Accessibility labels and `<select id="wake-preset">` are properly hidden with `.visually-hidden`, removing duplicate visible text and unstyled dropdowns.
2. Steward Desk offers seamless switching between `💬 Conversation`, `🛡️ Standing Watches`, and `📋 Intelligence Feed`.
3. Conversation view connects to personal agent conversations, displays chat history, supports sending messages, and provides 1-click prompt cards.
4. Standing Watches view provides 1-click templates, elevated watch cards with live action buttons (*Wake now*, *Pause/Resume*, *Close*), and a clean, categorized composer.
5. Intelligence Feed view presents formatted observation cards.
6. All automated tests pass (`python3 -m unittest discover -s tests -v`).
7. `./scripts/validate-repo.sh` and `./tests/test_structure.sh` pass.

## Validation Plan

- Automated: `python3 -m unittest discover -s tests -v`
- Lint/Structure: `./tests/test_structure.sh`, `./scripts/validate-repo.sh`
- Manual: Browser validation of tabs, prompt cards, message sending, watch creation, wake trigger, and clean styling.

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** No
- **Privileged tools expected?** none (ADR 0018)
- **May run on Air?** Yes (web assets and tests only)

## Closeout

- Verification evidence:
  - `./tests/test_structure.sh`: PASS (RESULT: OK)
  - `./scripts/validate-repo.sh`: PASS (RESULT: OK)
  - `python3 -m unittest discover -s tests -v`: 421 tests passed (0 failures, 2 skipped)
- Follow-ons filed: none
- Residual risks: none
- Docs/status updated: `docs/work-orders/README.md`
- Status surfaces reconciled: yes
- Summary metadata reviewed: yes
- Planning-only change? No
- Host deploy performed? No (pending operator review and authorization)

