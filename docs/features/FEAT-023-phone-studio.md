# FEAT-023 — Phone Studio

- **Status:** Complete (Code in Git)
- **Created:** 2026-10-18
- **Owner:** operator
- **GitHub issue:** draft only

## Purpose

Let the operator use the lab from an iPhone. The phone joins the existing tailnet and opens Studio in Safari. Chat, a streaming reply, and one tool approval have to fit a phone screen. Add to Home Screen can name that page. This is the same control plane, not a native app and not a model on the phone.

## User workflow

1. Put the Tailscale app on the iPhone and join the lab tailnet. That install is an operator action. This feature does not change Tailscale ACLs.
2. Open the mini control plane in Safari at the address already used from the Air.
3. Sign in with the existing operator login.
4. See a full-width chat. The sidebar opens as a drawer and starts closed.
5. Send a message and read the reply.
6. When a run is waiting, open it and tap Approve or Deny with the proposed action visible.
7. Optionally use Add to Home Screen so the same page opens under the lab name.

## Target host(s)

| Role | Host alias | Why |
|------|------------|-----|
| Control plane | `mac-mini` | Already serves Studio at `/` |
| Browser | iPhone on the tailnet | Human client. Not a new lab host and not an inference device |

## Dependencies

- Features: `FEAT-004` (the unchecked phone criterion lives here now)
- ADRs / policies: ADR 0012 (Tailscale is the private network and is not application login), ADR 0034 (bind stays loopback or this host's Tailscale address)
- Hosts / services that must already be live: control plane on `mac-mini:8088`

## Proposed deliverables

- Phone layout in `platform/src/ai_lab_platform/web/agents.html`
- A small web app manifest and Home Screen title, if IWO-110 includes them
- A unit test that the phone layout contract is present
- This feature record and IWO-110

## Proposed implementation work orders

| ID (proposed) | Title | Depends on | Acceptance (sketch) |
|---------------|-------|------------|---------------------|
| [IWO-110](../work-orders/IWO-110-phone-studio-layout.md) | Phone Studio layout | FEAT-004 | At phone width the chat is full width, the composer clears the home indicator, and Approve or Deny is reachable |
| later | Session that survives closing Safari | IWO-110 | Separate order. Token storage is an auth change |
| later | Notice when a run is waiting | IWO-110 | Separate order. Lock-screen or push, if Safari is not enough |
| later | Native iOS client | IWO-110 | Separate order. Only if Home Screen Safari is not enough |

## Acceptance criteria

- [x] An iPhone-width Studio chat uses the full width, with the sidebar closed until opened
- [x] The composer stays visible above the home indicator and the keyboard (100dvh + safe-area insets)
- [x] Login, send, and Approve / Deny are usable with a thumb (>= 44px touch targets)
- [x] Desktop Studio layout stays as it is (260px column preserved)
- [x] The session token stays in `sessionStorage` under `ai_lab_token`
- [x] No new public listener, Tailscale ACL change, or service worker
- [ ] Human confirmation on an iPhone on the tailnet
- [x] Human approval before any host deploy

## Out of scope

- A native Swift app, Xcode project, TestFlight, or App Store listing
- A service worker or offline cache of authenticated pages
- Moving the session token to `localStorage` or a longer-lived cookie
- Push notifications
- Phone layouts for Classroom, Security, Jupyter, or the Agent Studio canvas
- Installing Tailscale, changing ACLs, or publishing the control plane to the public Internet
- Deploying or restarting the control plane

## Implementation status (honest)

| Layer | Status | Evidence |
|-------|--------|----------|
| Spec in Git | done | this file |
| Code | done | `agents.html`, `static/manifest.json`, `control_app.py`, `tests/test_phone_studio_layout.py` |
| Host deploy | not authorized | n/a |
| Live verified | no | waiting on human verification on iPhone |

## Notes

Verified on 2026-10-18 from the Studio page, not from an iPhone. `agents.html` sets a viewport. `.app` is a row. `.sidebar` is 260px. Collapse is only the ☰ button adding `.sidebar.collapsed` (`width: 0`), and that choice is not saved. Narrow rules exist for goal cards, prefs, dashboard grids, and message avatars. They do not turn the sidebar into a drawer. The composer is in normal flow with no `safe-area-inset`. `html, body` use `height: 100%`, not a dynamic viewport height. Login is the modal in `chrome.js`. The token is `sessionStorage` key `ai_lab_token`, so closing the Safari tab drops the session. IWO-109 is the Steward activity page, so this work is IWO-110.
