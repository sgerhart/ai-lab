#!/usr/bin/env bash
# Compare installed Studio models on a short fixture. Default is a plan only.
# --apply calls Ollama. Never pulls weights.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="${ROOT}/platform/src${PYTHONPATH:+:$PYTHONPATH}"
PYTHON="${ROOT}/platform/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON="python3"
fi
exec "$PYTHON" -m ai_lab_platform.model_bench --ollama "${OLLAMA_URL:-http://mac-studio:11434}" "$@"
