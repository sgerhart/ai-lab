#!/usr/bin/env bash
# Stdio MCP server for IDEs (FEAT-005 / IWO-042). Does not start the control plane.
# Requires: AI_LAB_API_TOKEN (or session bearer) and reachable AI_LAB_API_BASE.
set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="${ROOT}/platform/src${PYTHONPATH:+:$PYTHONPATH}"
export AI_LAB_API_BASE="${AI_LAB_API_BASE:-http://127.0.0.1:8088}"
if [[ -z "${AI_LAB_API_TOKEN:-}" ]]; then
  TOKEN_FILE="${AI_LAB_API_TOKEN_FILE:-}"
  if [[ -z "$TOKEN_FILE" ]]; then
    if [[ -f "${HOME}/.ai-lab/api.token" ]]; then
      TOKEN_FILE="${HOME}/.ai-lab/api.token"
    elif [[ -f "${HOME}/.ai-lab/mac-mini-api.token" ]]; then
      TOKEN_FILE="${HOME}/.ai-lab/mac-mini-api.token"
    fi
  fi
  if [[ -n "$TOKEN_FILE" && -f "$TOKEN_FILE" ]]; then
    AI_LAB_API_TOKEN="$(tr -d '\n' <"$TOKEN_FILE")"
    export AI_LAB_API_TOKEN
  fi
fi
exec python3 -m ai_lab_platform.lab_mcp_server
