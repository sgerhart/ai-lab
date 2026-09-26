#!/usr/bin/env bash
# Send a short DefenseClaw summary to the mini. Default is print-only.
# --apply posts to the lab API. Never prints or sends config.yaml, device.key, or audit.db.
set -euo pipefail
export PATH="${HOME}/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

APPLY=0
for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=1 ;;
    --help|-h)
      cat <<'EOF'
Usage: ./scripts/defenseclaw-report.sh [--apply]

Prints DefenseClaw posture JSON: versions, agents, the operator config
(secret values withheld), guardrail, finding titles, and block or confirm totals.
--apply POSTs it to ${AI_LAB_URL:-http://mac-mini:8088}/v1/security/posture
using the bearer token in ~/.ai-lab/api.token, or ~/.ai-lab/mac-mini-api.token.
Does not send config.yaml, the device key, or audit.db.
EOF
      exit 0
      ;;
    *)
      echo "unknown arg: $arg" >&2
      exit 2
      ;;
  esac
done

if ! command -v defenseclaw >/dev/null 2>&1; then
  echo "defenseclaw: NOT FOUND on PATH" >&2
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="${ROOT}/platform/src${PYTHONPATH:+:$PYTHONPATH}"
JSON="$(python3 - <<'PY'
import json, subprocess
from pathlib import Path
from ai_lab_platform.defenseclaw_report import (
    build_report,
    read_block_episodes,
    read_decision_summary,
    read_finding_summary,
)

def run(args):
    proc = subprocess.run(args, check=False, capture_output=True, text=True)
    return (proc.stdout or "") + (proc.stderr or "")

home = Path.home() / ".defenseclaw"
config_path = home / "config.yaml"
config_text = config_path.read_text(encoding="utf-8") if config_path.is_file() else ""
report = build_report(
    version_text=run(["defenseclaw", "version"]),
    status_text=run(["defenseclaw", "status"]),
    alerts_text=run(["defenseclaw", "alerts", "--limit", "8", "--no-tui"]),
    guardrail_text=run(["defenseclaw", "guardrail", "status"]),
    config_text=config_text,
    findings=read_finding_summary(home / "audit.db"),
    decisions=read_decision_summary(home / "audit.db"),
    episodes=read_block_episodes(home / "audit.db"),
)
print(json.dumps(report))
PY
)"

if [[ "$APPLY" -eq 0 ]]; then
  echo "$JSON"
  echo "---"
  echo "dry-run. Re-run with --apply to send this summary to the mini."
  exit 0
fi

TOKEN_FILE="${HOME}/.ai-lab/api.token"
if [[ ! -f "$TOKEN_FILE" && -f "${HOME}/.ai-lab/mac-mini-api.token" ]]; then
  TOKEN_FILE="${HOME}/.ai-lab/mac-mini-api.token"
fi
if [[ ! -f "$TOKEN_FILE" ]]; then
  echo "missing ~/.ai-lab/api.token (or mac-mini-api.token)" >&2
  exit 1
fi
URL="${AI_LAB_URL:-http://mac-mini:8088}/v1/security/posture"
curl -sf -m 20 -X POST "$URL" \
  -H "Authorization: Bearer $(tr -d '\n' <"$TOKEN_FILE")" \
  -H "Content-Type: application/json" \
  --data "$JSON"
echo
