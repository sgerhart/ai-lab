#!/usr/bin/env bash
# M1 control-plane API. Loopback only. Does not start compose or mutate hosts.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$ROOT/platform/src${PYTHONPATH:+:$PYTHONPATH}"
HOST="${AI_LAB_BIND_ADDRESS:-127.0.0.1}"
PORT="${AI_LAB_API_PORT:-8088}"
if [[ "$HOST" != "127.0.0.1" && "$HOST" != "localhost" && "$HOST" != "::1" ]]; then
  echo "Refusing to bind control plane on $HOST (loopback only in this script)." >&2
  exit 2
fi
cd "$ROOT/platform"
if [[ -x .venv/bin/uvicorn ]]; then
  exec .venv/bin/uvicorn --factory ai_lab_platform.control_app:app_factory --host "$HOST" --port "$PORT"
fi
exec python3 -m uvicorn --factory ai_lab_platform.control_app:app_factory --host "$HOST" --port "$PORT"
