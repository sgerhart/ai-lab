# IWO-111 — Steward MCP tool access and workspace integration

**Status:** Complete (unit-tested)  
**Priority:** P2  
**Effort:** M  
**Owner:** operator  
**Feature:** FEAT-022, FEAT-017  
**Services / Areas:** platform

Canonical AI Lab implementation Work Order for connecting governed MCP read tools to Steward standing goals, and embedding the Steward desk into the primary workspace shell alongside Agent Studio.

## Problem

1. Steward ([FEAT-022](file:///Users/stevengerhart/workspace/github/sgerhart/ai-lab/docs/features/FEAT-022-steward.md)) is currently locked to a hardcoded 16-tool `SEE_TOOLS` set in `steward.py`. When a goal wakes, `steward.py` explicitly strips MCP server IDs (`run.mcp_server_ids = []`), and `agent_loop.py` strips MCP tools (`mcp_tools = []`). Steward cannot inspect external or local systems connected via MCP (e.g. Gmail, GitHub, Apple Notes, local file search).
2. The `/steward` desk is rendered on an isolated page (`steward.html`). Clicking Steward in the sidebar triggers a full page navigation away from the SPA shell, dropping the left sidebar, active chat session, and project context.
3. Agent Studio's Fleet view displays the personal agent ("Second Brain") but has no visibility into Steward's active watches.

## Decision Context

- **Chosen approach:**
  - **Permission Alignment:** Map MCP capabilities with `permission_class == "read"` bound to the `personal` agent directly into Steward's **See** class. Capabilities with `privileged` or `network` map to **Approval** or **Draft** and cannot execute unattended during a background wake.
  - **Wake Execution:** Preserve `mcp_server_ids` on the goal and pass them to `run.mcp_server_ids` during `enqueue_wake()`. In `agent_loop.py`, allow wake runs to execute allowed MCP read tools.
  - **Workspace Integration:** Embed the Steward Desk into the primary single-page app shell (`agents.html`) as `#pane-steward`, preserving the sidebar and chat state. Keep `/steward` accessible as a deep-link.
  - **Studio Fleet Link:** On the "Second Brain" Fleet card in Agent Studio, surface active Steward watches and provide direct navigation to the Steward desk.
- **Alternatives rejected:**
  - Merging Steward solely into a nested config form in Agent Studio. Rejected; Steward is an autonomous presence and standing companion, not just a configuration screen.
  - Allowing write/privileged MCP tools in unattended background wakes. Rejected; violates FEAT-022 and ADR 0018 (human approval required for mutation/send/spend/delete).

## What To Build / Fix

1. **`platform/src/ai_lab_platform/steward.py`**:
   - Update `classify_tool(name)` and `access_manifest(policy, mcp_servers)` to incorporate bound MCP read tools (`mcp/<server_id>/<tool_name>`).
   - Update `create_goal()` to allow MCP read tools, infer `mcp_server_ids`, and store them on the goal record.
   - Update `enqueue_wake()` to set `run.mcp_server_ids = goal.get("mcp_server_ids") or []`.
2. **`platform/src/ai_lab_platform/agent_loop.py`**:
   - In `_wake_tools()`, allow bound MCP read tools from `run.tool_ceiling`.
   - In `run_turn()`, do not wipe `mcp_tools` if wake tools include MCP capabilities.
3. **`platform/src/ai_lab_platform/web/agents.html` & `studio.js`**:
   - Add `#pane-steward` to `agents.html` containing the Steward desk (presence indicator, goal form, goals stack, and activity timeline).
   - Wire sidebar button `#nav-steward` to switch to `#pane-steward` within the SPA.
   - Render connected MCP read sources under "It may read" chips on the desk.
   - Add a badge/link on the Agent Studio Second Brain card to view Steward watches.
4. **Tests**:
   - Update `tests/test_steward.py` to verify MCP read tool classification, goal creation with MCP tools, and wake runs retaining `mcp_server_ids`.

## Expected Change Surface

- Expected: `steward.py`, `agent_loop.py`, `control_app.py`, `agents.html`, `studio.js`, `steward.js`.
- Tests: `tests/test_steward.py`, `tests/test_agent_loop.py`.
- Docs/status: `docs/features/FEAT-022-steward.md`, `docs/work-orders/README.md`.

## Out Of Scope

- Deploying to `mac-mini` or `mac-studio` (host deploy requires explicit human authorization).
- Swift macOS Menu Bar app implementation (deferred to IWO-112).
- Allowing write/send/delete tools in unattended background wakes without approval.

## Do NOT Change

- The See / Draft / Approval security model (ADR 0018, FEAT-022).
- Binds stay `127.0.0.1` or Tailscale mesh address.
- No secrets in Git.

## Acceptance Criteria

1. `access_manifest()` lists bound MCP tools with `permission_class == "read"` in the `see` list.
2. `create_goal()` allows valid MCP read tools and records `mcp_server_ids`.
3. Background wake enqueued by `enqueue_wake()` preserves `mcp_server_ids` on the `AgentRun`.
4. `agent_loop.py` permits execution of approved MCP read tools during a wake and denies unapproved/privileged MCP tools.
5. In `agents.html`, clicking "Steward" opens the Steward desk without reloading the browser or unmounting the chat session.
6. The Steward desk displays connected MCP tools under "It may read".
7. Unit tests pass: `python3 -m unittest tests.test_steward -v`.
8. `./scripts/validate-repo.sh` passes.

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** None
- **May run on Air?** Yes for unit tests and local web verification.

## Execution

- **Branch:** `iwo/111-steward-mcp-and-workspace-integration`
- **Risk tier:** P2
- **Pre-PR / pre-merge gate:** `./scripts/validate-repo.sh` and `python3 -m unittest tests.test_steward -v`
- **Depends on:** IWO-109
- **Human verification required:** Yes

## Verification Results

- `python3 -m unittest tests.test_steward -v`: 14 tests passed (including MCP tool classification, MCP wake retention, and UI integration).
- `python3 -m unittest discover -s tests -v`: 413 tests passed, 2 skipped.
- `./scripts/validate-repo.sh`: OK.
- `./scripts/preflight.sh`: OK.
- `./tests/test_structure.sh`: OK.

