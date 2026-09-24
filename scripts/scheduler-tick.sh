#!/usr/bin/env bash
# Call POST /v1/scheduler/tick on the control plane (FEAT-009 / IWO-030).
# Does not install LaunchAgents. Dry-run by default; pass --apply to POST.
set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

APPLY=0
HOST="${AI_LAB_SCHEDULER_HOST:-}"
PORT="${AI_LAB_API_PORT:-8088}"
TOKEN_FILE="${AI_LAB_API_TOKEN_FILE:-$HOME/.ai-lab/api.token}"

for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=1 ;;
    --help|-h)
      echo "Usage: $0 [--apply]"
      echo "  Default: print the curl command (dry-run)."
      echo "  --apply: POST /v1/scheduler/tick using ~/.ai-lab/api.token"
      echo "  Host: AI_LAB_SCHEDULER_HOST, else loopback if healthy, else Tailscale IPv4."
      exit 0
      ;;
  esac
done

if [[ -z "$HOST" ]]; then
  if curl -sf -m 2 "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then
    HOST="127.0.0.1"
  elif command -v tailscale >/dev/null 2>&1; then
    HOST="$(tailscale ip -4 2>/dev/null | head -1 || true)"
  fi
fi
if [[ -z "$HOST" ]]; then
  HOST="127.0.0.1"
fi

URL="http://${HOST}:${PORT}/v1/scheduler/tick"
CMD=(curl -sS -m 120 -X POST "$URL" -H "Authorization: Bearer \$(cat $TOKEN_FILE)")

if [[ "$APPLY" -ne 1 ]]; then
  echo "dry-run: would run:"
  printf '  %s\n' "${CMD[*]}"
  echo "Pass --apply to execute (requires control plane + api.token)."
  exit 0
fi

if [[ ! -f "$TOKEN_FILE" ]]; then
  echo "missing token file: $TOKEN_FILE" >&2
  exit 1
fi
TOKEN=$(tr -d '\n' <"$TOKEN_FILE")
curl -sS -m 120 -X POST "$URL" -H "Authorization: Bearer ${TOKEN}"
echo
