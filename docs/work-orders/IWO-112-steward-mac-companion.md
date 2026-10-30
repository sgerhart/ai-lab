# IWO-112 — Steward Mac menu bar companion

**Status:** Complete (unit-tested)  
**Priority:** P2  
**Effort:** M  
**Owner:** operator  
**Feature:** FEAT-022, FEAT-010  
**Services / Areas:** clients, platform, hosts

Canonical AI Lab implementation Work Order for a native macOS Menu Bar companion for Steward, enabling quick-handoff of standing responsibilities, live breathing presence, desktop notifications, and a governed local Mac MCP bridge.

## Problem

1. Steward ([FEAT-022](file:///Users/stevengerhart/workspace/github/sgerhart/ai-lab/docs/features/FEAT-022-steward.md)) runs its background loop and wake scheduler on the always-on `mac-mini` (ADR 0037). On the operator's primary workstation (`m3-air`), checking on Steward or handing it a quick responsibility currently requires opening a browser, authenticating, and navigating into `/steward` or the Agent Studio.
2. When Steward finishes an unattended wake, drafts an observation, or pauses because a tool requires human approval, the operator receives no ambient desktop alert unless the browser tab happens to be active.
3. The operator has personal notes, markdown files, and local system context on the laptop that Steward cannot currently read because the control plane runs on the headless mini without access to the laptop's filesystem.

## Decision Context

- **Chosen approach:**
  - **Native macOS Menu Bar Extra (`clients/steward-mac`)**: A lightweight Swift/SwiftUI application living in the macOS status bar (`NSStatusItem`).
  - **Ambient Presence Dot**: Displays Steward's real-time heartbeat and presence (`Quiet` 🟢 / `Awake` 🔵 / `Paused` ⚪ / `Attention` 🟠) directly in the menu bar.
  - **Quick Handoff HUD Popover**: Clicking the menu bar item (or pressing a global hotkey) drops a floating HUD popover with:
    - Quick goal submission ("What should Steward keep watch on?", rhythm selector, allowed sources).
    - Active watches list with 1-click Pause/Resume/Wake Now.
    - Recent activity timeline and observation snippets.
    - 1-click deep link to open the full desk in the default browser (`http://<host>:8088/?open=steward`).
  - **Native Notifications**: Delivers desktop notifications via UserNotifications when a wake completes or an approval is required.
  - **Local Mac MCP Bridge (`scripts/steward-mac-bridge.py`)**: A lightweight, governed read-only MCP server running on the Mac that exposes local markdown notes (`mac_notes_list`, `mac_notes_read`, `mac_notes_search`) and laptop system status (`mac_system_status`). Because its tools are marked `permission_class = "read"`, they seamlessly integrate into Steward's **See** ceiling under IWO-111.
  - **Always-on Host Boundary Preserved**: The companion is strictly a client. The scheduler, model execution, and persistent storage remain on the `mac-mini` (ADR 0037). Closing the laptop lid does not terminate Steward's standing life.
- **Alternatives rejected:**
  - Running the control plane and background scheduler on the MacBook Air. Rejected; the Air sleeps when closed, violating the standing life requirement of FEAT-022 and ADR 0037.
  - Heavy Electron/Chromium wrapper app. Rejected; consumes 500+ MB RAM for a menu bar icon. A native Swift/AppKit app compiles to a lightweight binary (~5 MB) with negligible idle CPU and RAM.
  - Unauthenticated local bridges. Rejected; requests require token authentication or local loopback binding.

## What To Build / Fix

1. **`clients/steward-mac`**:
   - `Package.swift`: Swift package definition for macOS 14+ (Sonoma/Sequoia).
   - `Sources/StewardCompanion/App.swift`: `NSApplication` / SwiftUI `MenuBarExtra` lifecycle.
   - `Sources/StewardCompanion/StewardClient.swift`: Asynchronous HTTP client communicating with `mac-mini:8088` (or configurable host via preferences/env `STEWARD_HOST` and `STEWARD_TOKEN`).
   - `Sources/StewardCompanion/Views/MenuBarView.swift`: Presence indicator icon and menu bar status item.
   - `Sources/StewardCompanion/Views/PopoverHUDView.swift`: Glassmorphic HUD popover with quick goal creation, active goals list, pause/resume controls, and activity feed.
   - `build.sh`: Build script compiling the application and producing `Steward.app`.
2. **`scripts/steward-mac-bridge.py` & `platform/src/ai_lab_platform/mac_bridge.py`**:
   - Standard stdio-based MCP server providing read-only personal tools (`mac_notes_list`, `mac_notes_read`, `mac_notes_search`, `mac_system_status`).
   - Declares read-only capabilities with `permission_class: "read"` compatible with Steward's See ceiling.
3. **Tests & Runbooks**:
   - `tests/test_steward_mac_bridge.py`: Tests for the local Mac MCP bridge tool definitions, read operations, and safety bounds (denial of writes, path traversal prevention).
   - `hosts/m3-air/RUNBOOK.md`: Add instructions for building and launching the companion app on the Air.

## Expected Change Surface

- Expected: `clients/steward-mac/`, `scripts/steward-mac-bridge.py`, `platform/src/ai_lab_platform/mac_bridge.py`, `hosts/m3-air/RUNBOOK.md`.
- Tests: `tests/test_steward_mac_bridge.py`.
- Docs/status: `docs/features/FEAT-022-steward.md`, `docs/work-orders/README.md`.

## Out Of Scope

- Deploying to `mac-mini` or `mac-studio` (host deploy requires explicit human authorization).
- Writing or mutating local files from the Mac MCP bridge (all bridge tools are read-only).
- Modifying the mini scheduler or ADR 0037 always-on placement.

## Do NOT Change

- Binds stay `127.0.0.1` or Tailscale mesh address.
- No secrets in Git.
- The See / Draft / Approval security model (ADR 0018, FEAT-022).

## Acceptance Criteria

1. `clients/steward-mac` compiles successfully using `swift build` or `./clients/steward-mac/build.sh` on macOS.
2. The companion connects to the control plane API (`/health`, `/v1/steward/goals`, `/v1/steward/activity`).
3. `mac_bridge.py` provides read-only MCP tools (`mac_notes_list`, `mac_notes_read`, `mac_notes_search`, `mac_system_status`) with path traversal guards.
4. Unit tests pass: `python3 -m unittest tests.test_steward_mac_bridge -v`.
5. `./scripts/validate-repo.sh` passes.

## Validation Plan

- Automated: `python3 -m unittest discover -s tests -v` and `./scripts/validate-repo.sh`.
- Manual: Compile `Steward.app` on the Air and test the menu bar icon and HUD popover against the local platform harness.

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** None
- **May run on Air?** Yes (designed specifically as the Air operator companion).

## Execution

- **Branch:** `iwo/112-steward-mac-companion`
- **Risk tier:** P2
- **Pre-PR / pre-merge gate:** `./scripts/validate-repo.sh` and `python3 -m unittest discover -s tests -v`
- **Depends on:** IWO-111
- **Human verification required:** Yes

## Verification Results

- `clients/steward-mac/build.sh`: Successfully compiled with Swift 6 and packaged `dist/Steward.app` with `Info.plist` (0 warnings).
- `python3 -m unittest tests.test_steward_mac_bridge -v`: 8 tests passed (path traversal prevention, size truncation, search, system status, MCP capability schema).
- `python3 -m unittest discover -s tests -v`: 421 tests passed (2 skipped).
- `./scripts/validate-repo.sh`: OK.
- `./scripts/preflight.sh`: OK.
- `./tests/test_structure.sh`: OK.

