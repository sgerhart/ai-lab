#!/usr/bin/env bash
# Harness-only eval dry-run. Never pulls weights.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$ROOT/platform/src${PYTHONPATH:+:$PYTHONPATH}"
for arg in "$@"; do
  if [[ "$arg" == "--pull" || "$arg" == "--download" ]]; then
    echo "Refusing to pull weights. See docs/runbooks/adding-a-model.md" >&2
    exit 2
  fi
done
PYTHON="${ROOT}/platform/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON="python3"
fi
exec "$PYTHON" -m ai_lab_platform.eval_dry_run "$@"
