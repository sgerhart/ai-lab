#!/usr/bin/env bash
# Stdio MCP server for IDEs (FEAT-005 / IWO-042). Does not start the control plane.
# Requires: AI_LAB_API_TOKEN (or session bearer) and reachable AI_LAB_API_BASE.
set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="${ROOT}/platform/src${PYTHONPATH:+:$PYTHONPATH}"
export AI_LAB_API_BASE="${AI_LAB_API_BASE:-http://127.0.0.1:8088}"
if [[ -z "${AI_LAB_API_TOKEN:-}" && -f "${HOME}/.ai-lab/api.token" ]]; then
  AI_LAB_API_TOKEN="$(tr -d '\n' <"${HOME}/.ai-lab/api.token")"
  export AI_LAB_API_TOKEN
fi
exec python3 -m ai_lab_platform.lab_mcp_server
