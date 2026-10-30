# IWO-110 — Phone Studio layout

**Status:** Draft  
**Priority:** P2  
**Effort:** S  
**Owner:** operator  
**Feature:** FEAT-023  
**Services / Areas:** platform

## Problem

Studio at `/` cannot be used on an iPhone. The page is a side-by-side shell, and the narrow-screen rules do not fix that shell.

Evidence from `platform/src/ai_lab_platform/web/agents.html` and `platform/src/ai_lab_platform/web/static/chrome.js` (read 2026-10-18; no iPhone session):

- `.app` is `display: flex`. `.sidebar` is `width: 260px`. `.sidebar.collapsed` is `width: 0`.
- Collapse is only `toggleSidebar()` on `#toggle-side` and `#show-side`. It is not saved, and nothing starts the sidebar collapsed.
- `@media (max-width: 680px)` stacks `.goal-grid`. `@media (max-width: 720px)` stacks prefs and dashboard grids and hides message avatars. `@media (max-width: 900px)` stacks the artifact editor. None of these change `.sidebar` or `.app`.
- At a 390px-wide phone, a 260px sidebar leaves about 130px for the chat.
- `.composer-dock` is in normal flow (`flex: 0 0 auto`, padding `8px 16px 12px`). There is no `safe-area-inset`.
- `html, body` set `height: 100%`. Safari's toolbar can cover the composer.
- Login is `#ai-lab-login-modal` in `chrome.js`. The card is `width: min(380px, 100%)`.
- The session token is `sessionStorage` key `ai_lab_token`.
- Approve and Deny are `#approve-action` and `#deny-action` on `#pane-run`, reached from Activity.
- FEAT-004 still leaves the phone criterion open. There is no web app manifest and no `apple-mobile-web-app-title`.

## Decision Context

- Chosen approach: adjust the existing Studio page so a phone width gets a full-width chat. The sidebar becomes a drawer and starts closed at that width. The composer clears the home indicator. Add a manifest and a Home Screen title for the same page. Keep the current routes, login, and `sessionStorage` token.
- Alternatives rejected: a native Swift app, a second mobile-only HTML page, a service worker, and moving the token to `localStorage` in this order.
- Assumptions: the operator installs Tailscale on the iPhone. The control plane stays at the address already used from the Air. This order does not invent a URL, change a bind, or change a Tailscale ACL.
- Open decisions:
  - Breakpoint. Recommend `720px`, matching the existing prefs and dashboard rules. A stricter phone-only width is the other option.
  - Drawer behavior. Recommend: under the breakpoint the sidebar starts closed on each load, overlays the chat, and a tap outside closes it. Desktop widths keep today's sidebar.
  - Approval. Recommend: keep `#pane-run` and its Approve / Deny buttons. This order makes that pane reachable. An approval card inside the transcript is a later order.

## What To Build / Fix

- In `agents.html`, under the phone breakpoint:
  - The sidebar overlays the chat and starts closed. Chat uses the full width.
  - The shell uses a dynamic viewport height so Safari's toolbar does not cover the composer.
  - Composer padding includes `safe-area-inset-bottom`.
  - `#toggle-side`, `#show-side`, the send control, `#approve-action`, and `#deny-action` are at least 44px on a side.
  - The composer hint does not tell a phone user to press Enter.
- Add a static web app manifest and an `apple-mobile-web-app-title` of `AI LAB`, pointing at `/`. Serve the manifest from the control plane if it is not already a static file.
- Leave login, `/v1` routes, and `sessionStorage` `ai_lab_token` as they are.
- A unit test reads `agents.html` (and the manifest) and checks the phone contract: a max-width rule that overlays or hides the sidebar, a safe-area padding on the composer, and the Home Screen title. Follow the HTML-read style in `tests/test_agent_studio_shell.py`.

## Expected Change Surface

- Expected: `agents.html`, a small manifest, possibly the static-file route that already serves `/static`, one test module, this feature's status lines.
- Tests: a new test module, or a case added beside the Studio shell tests.
- Docs/status: `docs/features/FEAT-023-phone-studio.md`, `docs/features/index.md`, this file's Closeout when the work is done.

## Out Of Scope

- Native iOS, Xcode, TestFlight, App Store
- Service worker or offline cache
- Changing where the session token is stored, or how long it lives
- Push or lock-screen notices
- Phone layouts for Classroom, Security, Jupyter, or the Agent Studio canvas
- Host deploy, control-plane restart, Tailscale ACL edits, new bind addresses
- Inline approval inside the chat transcript

## Do NOT Change

- No secrets in Git.
- No `0.0.0.0` bind. No public reverse proxy.
- Desktop widths keep the current 260px sidebar until the operator collapses it.
- Approve and Deny still show the proposed action and still call the existing approve-action route.
- `sessionStorage` key `ai_lab_token` stays the session store.
- No runtime work-order rows.

## Acceptance Criteria

1. At `720px` and below, the sidebar does not take a column beside the chat, and a fresh load starts with it closed.
2. The composer padding accounts for `safe-area-inset-bottom`, and the page shell uses a dynamic viewport height.
3. Send, the sidebar control, Approve, and Deny are at least 44px in that layout.
4. A manifest and Home Screen title name the lab and start at `/`.
5. Wider than the breakpoint, the sidebar is still the 260px column.
6. The test for that contract passes, and `./scripts/validate-repo.sh` passes.
7. An operator pass on an iPhone, over Tailscale, confirms login, send, a visible reply, and Approve or Deny. That pass is human verification. It is not authorized by accepting this draft.

## Validation Plan

- Automated: the new unit test, then `./scripts/validate-repo.sh`.
- Manual: on an iPhone on the tailnet, open Studio, sign in, send a chat, and open a waiting run. Also glance at a desktop-width window and confirm the sidebar is unchanged.
- Evidence to include: the unit-test result. The iPhone pass is recorded in Closeout only after the operator does it. This draft does not perform it.

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none
- **May run on Air?** No — this does not start lab compose. The page is served by the control plane.

## Execution

- **Branch:** `iwo/110-phone-studio-layout`
- **Risk tier:** P2
- **Pre-PR / pre-merge gate:** the new unit test and `./scripts/validate-repo.sh`
- **Depends on:** FEAT-004 Studio at `/`
- **Human verification required:** Yes — iPhone Safari on the tailnet
- **Reviewer / approver:** operator
- **Project status record:** `docs/features/index.md`
- **Other status surfaces:** `docs/features/FEAT-023-phone-studio.md`

## Closeout

- Verification evidence: not started. This file is a draft.
- Follow-ons filed: session lifetime, a waiting-run notice, and a native client stay proposed on FEAT-023. Not separate files.
- Residual risks: not started.
- Docs/status updated: spec and index only.
- Status surfaces reconciled: index lists FEAT-023 and IWO-110 as Draft / Specified.
- Summary metadata reviewed: yes
- Planning-only change? Yes
- Host deploy performed? No
