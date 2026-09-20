#!/usr/bin/env bash
# Health checks. Default: repository only. --live probes listeners (read-only).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LIVE=0
[[ "${1:-}" == "--live" ]] && LIVE=1

echo "repo: $ROOT"
if [[ "$LIVE" -eq 0 ]]; then
  echo "live probes skipped (pass --live to curl loopback health endpoints)"
  exit 0
fi

fail=0
probe() {
  local url="$1"
  if command -v curl >/dev/null; then
    if curl -fsS --max-time 2 "$url" >/dev/null; then
      echo "OK $url"
    else
      echo "DOWN $url"
      fail=1
    fi
  fi
}

# Defaults assume this machine is the service host with loopback publish.
probe "http://127.0.0.1:11434/api/tags"
# Postgres/qdrant are expected DOWN until compose is authorized.
echo "note: control-plane ports are expected down until compose is started"
exit "$fail"
