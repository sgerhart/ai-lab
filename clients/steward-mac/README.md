# Steward macOS Desktop App

Native macOS desktop companion application for **Steward** ([FEAT-022](../../docs/features/FEAT-022-steward.md)), the personal agent's standing desk.

Provides a full native macOS desktop experience (Dock app with window split-view) centered around a **conversational companion desk**, rich standing watch management, activity timeline, and local Mac note access.

## Architecture & Boundaries

- **Always-on Host Separation ([ADR 0037](../../docs/decisions/0037-mini-owns-personal-agent-loop.md)):** The background scheduler, agent loop, and persistent store run on the always-on `mac-mini`. The desktop app on `m3-air` is purely an operator client. Closing the laptop lid does not terminate Steward's standing life.
- **Governed Tool Ceiling:** Unattended background wakes execute only **See**-class tools. The local Mac MCP bridge (`scripts/steward-mac-bridge.sh`) exposes read-only tools (`mac_notes_list`, `mac_notes_read`, `mac_notes_search`, `mac_system_status`).
- **Native Swift/SwiftUI:** Built using pure Swift 6 and SwiftUI with native `NavigationSplitView`, unified toolbar, Apple SF Pro typography, and dark glassmorphic vibrancy.

## Features

1. **Conversational Companion Desk (`Desk`):**
   - Natural, conversational chat directly with Steward (`personal` agent).
   - Talk through daily tasks, ask what it observed during wakes, or hand off responsibilities naturally:
     - *"Keep watch on classroom notes daily and notify me of updates."*
     - *"What did you observe in your latest wake?"*
     - *"Search vault and local notes for recent ideas."*
   - Inline action buttons to turn discussed topics into standing watches.
   - Distinctive visual styling with frosted cards, presence glow, and tool execution callouts.

2. **Standing Watches Manager (`Standing Watches`):**
   - Visual cards showing each registered standing goal.
   - Shows wake rhythm (`HOURLY`, `DAILY`, `MANUAL`), active status badge, and allowed read sources.
   - Latest observation notes from previous wakes.
   - Instant controls: `Wake Now`, `Pause`, `Resume`, and `Close`.
   - Dedicated "+ Add Watch" modal sheet.

3. **Activity Timeline (`Activity Timeline`):**
   - Chronological log of background wake runs, executed tools, and filed observation dossiers.

4. **Local Mac Context & Hardware (`Mac Notes & Bridge`):**
   - Instant search and preview of local markdown notes on your Mac (`~/.ai-lab/notes/`).
   - Live hardware status card displaying laptop battery %, AC power source, and machine hostname.

5. **Minimalist Menu Bar Extra:**
   - Small SF Symbol (`sparkles`) in the macOS menu bar indicating Steward's heartbeat without taking up menu bar text space.

6. **Connection Settings:**
   - Switch between `mac-mini:8088` (Lab Mini) and `127.0.0.1:8088` (Local harness) with 1-click presets.
   - Automatically detects bearer tokens from `~/.ai-lab/mac-mini-api.token` and `~/.ai-lab/api.token`.

## Building & Running

### Requirements

- macOS 14+ (Sonoma or Sequoia)
- Apple Swift 5.9+ (included with Xcode or Command Line Tools)

### Build

```bash
cd clients/steward-mac
./build.sh
```

This compiles the release binary and packages `dist/Steward.app`.

### Launch

```bash
open dist/Steward.app
```

To install permanently into your user Applications:

```bash
cp -R dist/Steward.app ~/Applications/
```

### Local Mac MCP Bridge

To allow Steward on the mini to inspect notes or system status on this Mac:

```bash
./scripts/steward-mac-bridge.sh
```
