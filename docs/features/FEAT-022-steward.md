# FEAT-022 — Steward

- **Status:** Live on the mini (desk served 2026-10-21; a wake has not been watched there)
- **Created:** 2026-10-18
- **Owner:** operator
- **GitHub issue:** draft only

## Purpose

Give the personal agent a standing life on the Mac mini. The operator hands it a responsibility. Between conversations it wakes, looks at the work it is allowed to see, and leaves a result or a question. The product name is **Steward**. It is the existing `personal` agent, not a second identity and not a mascot.

The Steward should know the operator's lab work. It does not receive every file, credential, or adjacent system on the machines. New sources are named grants. Actions that leave the machine, spend money, delete, or change what runs unattended still stop for the operator.

## User workflow

1. Open the personal agent chat.
2. Open `/steward` and hand it a responsibility in plain language ("keep the classroom notes current", "watch this research question"). Choose how often it wakes and what it may read.
3. See the goal on the same page, and later the note a wake brings back.
4. Close the laptop. The mini scheduler wakes the goal when it is due.
5. Reopen the lab and read the activity: what it looked at, what it drafted, and what it needs decided.
6. Pause it, wake it again, or close it on that page. Closing asks first. A closed goal stays closed.

## Access

Three classes. A goal cannot promote a tool into a wider class.

| Class | What it means | Default contents |
|-------|----------------|------------------|
| **See** | Read during a background wake. No messages sent, no files written, no schedules changed. | Personal chat history and filed day notes. Memory vault (`vault_list`, `vault_grep`, `vault_read`). Notes (`files_list`, `files_grep`, `files_read`). Reports (`report_list`, `report_read`). Nexus search (`nexus_search`). Public web lookup (`web_search`). Presentation and skill lists and skill read. Schedule list. Lab health read. |
| **Draft** | Write a local artifact when the operator is in the conversation, or when that goal explicitly allows a draft. The draft waits. It is not sent. | `vault_write`, `report_write`, `presentation_write`, `skill_create`, `research` (it files a source dossier). |
| **Approval** | The loop stops until the operator records approval (ADR 0018). | `schedule_create`, `schedule_cancel`. `consult_frontier` (may bill). Any future send, spend, delete, push, merge, or deploy. |

**Never in the prompt or the tool list:** secret store contents, API keys, SSH keys, cookies, passwords, DefenseClaw device material, and credentials for adjacent stacks (Clarion, the factory, trading). A tool may use a saved secret without placing the secret in the model context. That path does not exist yet and is not part of the first work order.

**Not connected.** These are the rest of "everything I do." Each one is a later grant, off until its own work order:

- Mail, calendar, browser history, and messages
- The home directory and git repositories other than the authorized lab workspace
- Classroom sessions (transcripts are not saved today)
- The coding assistant's workspace, beyond the read tools that agent already has
- Computer control, and any adjacent product stack

Background wakes use the **See** list only. A wake that needs a draft or an approval records the need and stops.

## Target host(s)

| Role | Host alias | Why |
|------|------------|-----|
| Harness, goals, wakes | `mac-mini` | Always-on plane (ADR 0009, ADR 0037) |
| Inference | `mac-studio` | Local model for a wake. No silent paid fallback (ADR 0038) |
| Human | `mac-air` | Chat and review. Need not stay awake |

## Dependencies

- Features: FEAT-010 (personal loop), FEAT-009 (scheduler tick), FEAT-002 (durable runs)
- ADRs / policies: ADR 0018, ADR 0037, ADR 0038. `agents/personal/policy.json` stays the tool list. The manifest narrows it for a wake; it does not add tools.
- Hosts / services that must already be live: none for the spec. A later wake needs the mini scheduler and a local model.

## Proposed deliverables

- Access manifest and standing-goal records
- Scheduler marks a due goal without calling a model
- A later wake enqueues one bounded read-only run and writes an activity entry
- Activity list in the lab UI
- Tests for class boundaries: a goal cannot grant **Never**, and a background wake cannot call **Draft** or **Approval**

## Proposed implementation work orders

| ID (proposed) | Title | Depends on | Acceptance (sketch) |
|---------------|-------|------------|---------------------|
| [IWO-107](../work-orders/IWO-107-steward-access-and-goals.md) | Access manifest and standing goals | FEAT-010, FEAT-009 | Goals persist. A wake allow-list is See only. Tick marks a goal due and does not call a model. |
| [IWO-108](../work-orders/IWO-108-steward-readonly-wake.md) | Read-only wake | IWO-107 | A due goal enqueues one bounded personal run and records activity. |
| [IWO-109](../work-orders/IWO-109-steward-activity-page.md) | Activity in the lab UI | IWO-108 | The operator can read, pause, and close a goal from the lab. |
| [IWO-111](../work-orders/IWO-111-steward-mcp-and-workspace-integration.md) | Steward MCP tool access and workspace integration | IWO-109 | Bound MCP read tools qualify for See class; workspace integration; Second Brain link. |
| [IWO-112](../work-orders/IWO-112-steward-mac-companion.md) | Steward Mac menu bar companion | IWO-111 | Native macOS menu bar extra, HUD popover, notifications, and local Mac MCP bridge. |
| later | One grant per outside source | IWO-111 | Mail, calendar, repos, or another named source, each its own order. |

## Acceptance criteria

- [x] The operator can create, list, pause, resume, and close a standing goal (API, unit-tested). A closed goal stays closed.
- [x] `background_tools` returns only the See list named on the goal
- [x] Draft, Approval, and unknown tools are refused on create and dropped by `background_tools`
- [x] A goal cannot add a Never source
- [x] A due goal enqueues one read-only run and an activity entry (IWO-108, unit-tested)
- [ ] Closing the Air does not drop the goal (not live-verified)
- [x] No new privileged tool and no secret in Git. This feature does not authorize a host deploy.

## Out of scope

- A second agent identity, a mascot, or the name Dot
- Slack, texting, voice calls, and a private computer the Steward drives
- Turning on mail, calendar, browser, home-directory, or adjacent-stack access in the first slice
- Send, spend, delete, push, merge, deploy
- Autonomously coding the lab (FEAT-007)

## Implementation status (honest)

| Layer | Status | Evidence |
|-------|--------|----------|
| Spec in Git | Specified | this file |
| Code | partial | Goals, See ceiling, queued wake, `/steward` desk (presence, rhythm, source chips, reversible pause). |
| Host deploy | done | 2026-10-21: desk page, script, `steward.py`, and `control_app.py` copied. `com.ai-lab.control-plane` restarted. |
| Live verified | partial | `GET http://mac-mini:8088/health` ok, role control-plane. `GET /steward` served the desk (`Keep watch`, presence, `steward.js?v=3`). `POST /v1/steward/goals/does-not-exist/resume` returned 404 unknown goal. A wake has not been watched on the mini. |

## Notes

The product name is Steward. The agent id stays `personal`.

Open decision that does not block IWO-107: goal records live in `~/.ai-lab/steward/goals.json` on the mini, the same pattern as schedule state. Move them into Postgres if a later order needs them in the authoritative store.
