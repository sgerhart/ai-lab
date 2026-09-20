#!/usr/bin/env bash
# Studio worker API. Loopback only. Does not pull models.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$ROOT/platform/src${PYTHONPATH:+:$PYTHONPATH}"
HOST="${AI_LAB_BIND_ADDRESS:-127.0.0.1}"
PORT="${AI_LAB_STUDIO_WORKER_PORT:-8090}"
if [[ "$HOST" != "127.0.0.1" && "$HOST" != "localhost" && "$HOST" != "::1" ]]; then
  echo "Refusing to bind studio worker on $HOST (loopback only in this script)." >&2
  exit 2
fi
cd "$ROOT/platform"
if [[ -x .venv/bin/uvicorn ]]; then
  exec .venv/bin/uvicorn --factory ai_lab_platform.studio_worker:app_factory --host "$HOST" --port "$PORT"
fi
exec python3 -m uvicorn --factory ai_lab_platform.studio_worker:app_factory --host "$HOST" --port "$PORT"
