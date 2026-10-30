#!/usr/bin/env bash
# Stdio MCP server for Steward personal tools on macOS (IWO-112).
# Exposes read-only markdown notes and host power/battery status.
set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="${ROOT}/platform/src${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m ai_lab_platform.mac_bridge
