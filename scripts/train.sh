#!/usr/bin/env bash
# Training is not authorized from this wrapper. No dataset downloads.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$ROOT/platform/src${PYTHONPATH:+:$PYTHONPATH}"
PYTHON="${ROOT}/platform/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON="python3"
fi
exec "$PYTHON" -m ai_lab_platform.train_refuse "$@"
