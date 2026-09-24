#!/usr/bin/env bash
# Antares / Studio preflight (FEAT-015 / IWO-047). Read-only by default.
set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STUDIO_OLLAMA="${STUDIO_OLLAMA_URL:-http://mac-studio:11434}"
STUDIO_JUPYTER="${STUDIO_JUPYTER_URL:-http://mac-studio:8888}"
APPLY_JUPYTER=0

for arg in "$@"; do
  case "$arg" in
    --jupyter-preflight) APPLY_JUPYTER=1 ;;
    --help|-h)
      echo "Usage: $0 [--jupyter-preflight]"
      echo "  Default: Ollama tags + port checks (no Jupyter kernel)."
      echo "  --jupyter-preflight: run scripts/studio-jupyter-exec.py --preflight"
      exit 0
      ;;
  esac
done

echo "studio_ollama=$STUDIO_OLLAMA"
if curl -sf -m 8 "${STUDIO_OLLAMA}/api/tags" >/tmp/ai-lab-ollama-tags.json; then
  python3 - <<'PY'
import json
from pathlib import Path
d = json.loads(Path("/tmp/ai-lab-ollama-tags.json").read_text())
names = [m.get("name") for m in d.get("models") or []]
print("ollama_models=", names)
print("antares_in_ollama=", any("antares" in (n or "").lower() for n in names))
PY
else
  echo "ollama_unreachable"
fi

echo "studio_jupyter=$STUDIO_JUPYTER"
code="$(curl -sS -m 8 -o /dev/null -w '%{http_code}' "$STUDIO_JUPYTER/" || true)"
echo "jupyter_http=$code"

echo -n "ssh_batchmode="
if ssh -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new \
  sgerhart@mac-studio 'echo ok' >/dev/null 2>&1; then
  echo ok
else
  echo fail
  echo "note: see docs/security/findings/F-015-studio-ssh-auth-failure.md"
fi

if [[ "$APPLY_JUPYTER" -eq 1 ]]; then
  if [[ ! -f "${HOME}/.ai-lab/studio-jupyter.token" ]]; then
    echo "missing ~/.ai-lab/studio-jupyter.token (run on mini)" >&2
    exit 1
  fi
  VENV="${AI_LAB_JUPYTER_EXEC_VENV:-$HOME/.ai-lab/venv-jupyter-exec}"
  if [[ ! -x "$VENV/bin/python" ]]; then
    /opt/homebrew/bin/python3 -m venv "$VENV"
    "$VENV/bin/pip" install -q websocket-client
  fi
  "$VENV/bin/python" "$ROOT/scripts/studio-jupyter-exec.py" --base "$STUDIO_JUPYTER" --preflight
fi

echo "ok"
