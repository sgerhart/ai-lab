# IWO-113 — Web UI & Steward Desk "Work of Art" Overhaul

**Status:** Complete (unit; not deployed)  
**Priority:** P1  
**Effort:** M  
**Owner:** human / Antigravity  
**Feature:** FEAT-004, FEAT-022  
**Services / Areas:** platform, docs  

Work Order Protocol Level 2 implementation order for redesigning the web interfaces hosted by `com.ai-lab.control-plane` on `m1-mini` into an elegant, user-friendly, state-of-the-art workspace.

## Problem

The web UI on `m1-mini:8088` (`agents.html` and `steward.html`) functionally supports Chat, Studio, and Steward, but visually feels like a simple prototype:
- Monolithic styling with flat dark rectangles and basic system fonts.
- Steward Desk lacks visual atmosphere, rich presence effects, and responsive feedback.
- Activity notes in "Brought back" are plain text blocks without structured metadata or syntax-highlighted findings.
- The sidebar and pane transitions lack modern micro-animations and depth.

## Decision Context

- **Design Aesthetic:** Premium dark-mode glassmorphism (`#070a10` / `#0d131f`), vibrant glows (electric indigo, cyan, emerald), `Outfit` + `Inter` typography with system fallbacks, and multi-layer breathing presence halos.
- **Unified Experience:** Seamless parity between the native Swift desktop app (`Steward.app`) and the web app (`agents.html` / `steward.html`).
- **Safety Boundaries:** Background wakes remain strictly within the **See** ceiling; mutations remain gated behind human approvals (ADR 0018, FEAT-022).
- **Host Deployment Gate:** Code is developed and tested in Git; live host deployment to `m1-mini` is deferred until explicitly authorized by the operator.

## What To Build / Fix

1. **Design Tokens & Typography:**
   - Add modern typography (`Outfit` for display headings, `Inter` for interface elements, `JetBrains Mono` for schedules and tokens).
   - Expand CSS design tokens in `chrome.css`, `steward.css`, and `agents.html` for glassmorphic panels, glowing border gradients, and elevation levels.

2. **Steward Desk Redesign (`steward.css`, `steward.js`, `steward.html`, `agents.html`):**
   - **Living Presence Halo:** Multi-ring breathing halo reflecting Quiet, Awake, or Paused states with radial gradients and subtle pulsing.
   - **Card Composer:** Frosted glass background, clear input focus styling, segmented schedule selector with natural-language rhythm preview, and categorized read-tool chips with icons.
   - **Standing Watches ("In Its Care"):** Elevated cards with live status badges, last wake relative timestamps, quick-action toolbar (*Wake now*, *Pause / Resume*, *Close*).
   - **Findings Timeline ("Brought Back"):** Vertical glowing timeline with status indicators, expandable notes, read-tool badges, and empty-state illustrations.

3. **Workspace Chrome & Sidebar Polish (`agents.html`, `chrome.css`):**
   - Sleek sidebar navigation with glowing active indicators, subtle dividers, and host status badges (`Mac mini · Studio Ollama (Live)`).
   - Polished Agent Studio fleet cards with glowing accents and direct handoffs.

4. **Validation:**
   - Ensure all automated platform tests pass (`python3 -m unittest discover -s tests -v`).
   - Run repo validation scripts (`./scripts/validate-repo.sh`, `./tests/test_structure.sh`).

## Expected Change Surface

- `platform/src/ai_lab_platform/web/static/steward.css`
- `platform/src/ai_lab_platform/web/static/steward.js`
- `platform/src/ai_lab_platform/web/static/chrome.css`
- `platform/src/ai_lab_platform/web/static/studio.css`
- `platform/src/ai_lab_platform/web/agents.html`
- `platform/src/ai_lab_platform/web/steward.html`
- `docs/work-orders/IWO-113-web-ui-and-steward-desk-overhaul.md`
- `docs/work-orders/README.md`

## Out Of Scope

- Modifying host launchd plists on `m1-mini`.
- Rewriting backend database schema or model providers.

## Do NOT Change

- See / Draft / Approval three-class security model.
- Port binds stay `127.0.0.1` or Tailscale IPv4; no `0.0.0.0`.
- No deployment to live hosts without operator confirmation.
