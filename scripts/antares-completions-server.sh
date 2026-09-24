#!/usr/bin/env bash
# Start Antares OpenAI-compatible completions server (FEAT-015 / IWO-048).
# Dry-run by default. Pass --apply to exec the Python server (foreground).
set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY_SCRIPT="$ROOT/scripts/antares-completions-server.py"
APPLY=0
HOST="${AI_LAB_BIND_ADDRESS:-127.0.0.1}"
PORT="${ANTARES_COMPLETIONS_PORT:-8001}"
MODEL_DIR="${ANTARES_MODEL_DIR:-$HOME/.ai-lab/antares/antares-1b}"
SERVED="${ANTARES_SERVED_MODEL_NAME:-antares-1b}"

for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=1 ;;
    --help|-h)
      echo "Usage: $0 [--apply]"
      echo "  Runs on Studio next to Antares weights. Refuses 0.0.0.0."
      exit 0
      ;;
  esac
done

echo "script=$PY_SCRIPT"
echo "host=$HOST port=$PORT"
echo "model_dir=$MODEL_DIR served=$SERVED"

if [[ "$HOST" == "0.0.0.0" || "$HOST" == "::" ]]; then
  echo "refusing all-interfaces bind" >&2
  exit 2
fi

if [[ "$APPLY" -ne 1 ]]; then
  echo "dry-run: would exec python3 $PY_SCRIPT --host $HOST --port $PORT"
  echo "Pass --apply to start (foreground)."
  exit 0
fi

if [[ ! -d "$MODEL_DIR" ]]; then
  echo "missing model dir: $MODEL_DIR" >&2
  exit 1
fi

# Prefer Studio Jupyter venv if present (torch/transformers).
CANDIDATES=(
  "$HOME/.ai-lab/jupyter/.venv/bin/python"
  /opt/homebrew/bin/python3
  python3
)
PY=""
for c in "${CANDIDATES[@]}"; do
  if [[ -x "$c" ]] || command -v "$c" >/dev/null 2>&1; then
    PY="$c"
    break
  fi
done
exec "$PY" "$PY_SCRIPT" --host "$HOST" --port "$PORT" --model-dir "$MODEL_DIR" --served-name "$SERVED"
