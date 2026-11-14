#!/bin/bash
set -euo pipefail
# Steward Gmail OAuth Authorization Helper

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON="$ROOT/platform/.venv/bin/python3"
if [ ! -x "$PYTHON" ]; then
  PYTHON="python3"
fi

export PYTHONPATH="$ROOT/platform/src:${PYTHONPATH:-}"
exec "$PYTHON" -m ai_lab_platform.gmail_auth "$@"

