#!/usr/bin/env bash
# Health checks. Default: repository only. --live probes listeners (read-only).
# Expected-down services do not fail the script until the lab is deployed.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LIVE=0
[[ "${1:-}" == "--live" ]] && LIVE=1

echo "repo: $ROOT"
if [[ "$LIVE" -eq 0 ]]; then
  echo "live probes skipped (pass --live to report loopback listeners)"
  exit 0
fi

probe() {
  local url="$1"
  local expect="$2"
  if ! command -v curl >/dev/null; then
    echo "SKIP $url (no curl)"
    return
  fi
  if curl -fsS --max-time 2 "$url" >/dev/null 2>&1; then
    echo "UP $url"
  else
    echo "DOWN $url ($expect)"
  fi
}

# Control-plane / worker ports are expected DOWN until authorized deploy.
probe "http://127.0.0.1:8088/health" "expected down until control-plane.sh"
probe "http://127.0.0.1:8090/health" "expected down until studio-worker.sh"
# Do not treat the Air Ollama wildcard listener as lab serving (F-003).
echo "note: Studio Ollama is probed on that host only; this laptop is not the compute plane"
exit 0
