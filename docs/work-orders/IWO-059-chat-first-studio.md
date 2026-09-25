# IWO-059 — Chat-first Studio shell

**Status:** In progress (code in the working tree; live operator pass not recorded)  
**Priority:** P2  
**Feature:** [FEAT-013](../features/FEAT-013-personal-agent-studio.md)  
**Design:** [ai-lab-chat-agent-ux/DESIGN-chat-first-agent-workspace.md](../../ai-lab-chat-agent-ux/DESIGN-chat-first-agent-workspace.md)

## What this slice does

Chat is the default. A new conversation is the AI Lab Assistant (`lab-operations`) without creating a preset. Jupyter and Activity sit in the main sidebar. Presets stay in the operator menu.

`GET /v1/capabilities` lists built-in tools and saved MCP servers. It does not spawn MCP processes. A saved server is `configured`, not `connected`. Privileged tools are `permission_required` and not permitted. Commands and arguments are omitted.

Send remains an ordinary chat reply. **Run in background** stores the prompt and queues an existing agent run on that conversation. The thread shows tool results and approval buttons. Restart recovery stays labeled not verified.

The Studio is the site root. `GET /` serves the chat workspace. `GET /agents` and `GET /lab` redirect to `/` (307). The old Lab connection hub is no longer a page. Jupyter still opens from **Jupyter Labs** in the sidebar. `/antares` stays its own page.

The sidebar keeps Status Dashboard and New chat fixed. A line sits under New chat, and another under Configure. Everything under the first line scrolls together: Jupyter Labs, Agents, MCP, Security, Configure, Projects, and Chats. Search is a magnifying-glass button beside AI LAB. The dialog looks across chats by name, and a project menu can narrow that list. All projects is the default, and a matching chat shows its project name. The menu button collapses the sidebar; the same button in the chat header opens it. Security has one badge, Antares, linking to `/antares`. Configure shows the AI badge. The sidebar brand is the flask icon plus a small AI LAB wordmark. Chat replies use the orb, and that image is the tab icon.

A project has a name, a description, and the chats added to it. After the first reply, a generic chat title is replaced by a short name from the same model. The payload stays a conversation title only.

Status Dashboard is the first sidebar item. `GET /v1/dashboard` (authenticated) reports mini memory and disk, Studio models on disk and in memory, and whether chat, Jupyter, Agents Studio, memory, frontier keys, MCP, the scheduler, and Antares are usable. Studio memory and disk come from the job helper's `GET /resources` when that route is running. The payload omits addresses, tokens, and MCP commands. The page checks when opened, on Check now, and every 5 minutes while it stays open.

## Not in this slice

Model pulls, host provisioning, paid calls, a new router, push/PR, or treating the isolated coding write path as the front door. Coding presets remain available and still require a separate copy plus exact approval.

## Acceptance

- [x] New chat does not require a preset
- [x] Capability payload omits MCP commands and does not mark an unprobed server connected
- [x] Background queue uses the existing run API
- [ ] Operator completes the lab-health scenario on the live mini and reopens it from another browser
