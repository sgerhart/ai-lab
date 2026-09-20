#!/usr/bin/env bash
# Wrapper: preflight then optional host setup.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOST=""
APPLY=0
FORCE=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --host) HOST="${2:-}"; shift ;;
    --apply) APPLY=1 ;;
    --force) FORCE=(--force) ;;
    --preflight|--dry-run) ;;
    *) echo "Usage: bootstrap.sh --host {m1-mini|studio|m3-air} [--apply] [--force]" >&2; exit 2 ;;
  esac
  shift
done
if [[ -z "$HOST" ]]; then
  echo "ERROR: --host is required" >&2
  exit 2
fi
"$ROOT/scripts/preflight.sh"
if [[ "$APPLY" -eq 1 ]]; then
  exec "$ROOT/scripts/host-setup.sh" --host "$HOST" --apply "${FORCE[@]}"
fi
exec "$ROOT/scripts/host-setup.sh" --host "$HOST" --preflight "${FORCE[@]}"
