# IWO-TBD-03 — Tool activity and approvals in chat
**Status:** Proposed · **Depends on:** IWO-TBD-01 and -02

## Objective
Make agent actions understandable in the conversation without forcing users into raw run traces.

## Work
1. Map existing run traces, tool results, pending actions, and approval endpoints into sanitized timeline events.
2. Display compact “server · tool · action · outcome” events with expandable technical detail.
3. Show exact-action approval/deny cards in chat, with target, arguments summary, risk, expiry, and action ID; use existing approval enforcement, never UI-only gates.
4. Redact secrets and avoid displaying raw tool outputs by default; preserve accessible status text.
5. Treat MCP server authorization separately from per-tool and per-action approval.

## Acceptance
- Actual used tools appear; merely connected tools do not masquerade as used.
- Approval is tied to exact pending action; denial blocks execution.
- Tool errors are visible and do not appear as success.
- No duplicate execution on approval refresh/reconnect.
- Tests cover denied/unlisted MCP tools and side-effecting calls.

## Out of scope / gates
No broad blanket approvals, write-capable coding, or new MCP transport.
