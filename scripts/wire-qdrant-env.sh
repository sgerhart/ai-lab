#!/usr/bin/env bash
# Wire QDRANT_* into ~/.ai-lab/start-control-plane.sh from compose.local.env (FEAT-008).
# Dry-run by default. Does not print secret values. Pass --apply to edit + restart API.
set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="${AI_LAB_COMPOSE_ENV:-$ROOT/infrastructure/compose.local.env}"
START="${HOME}/.ai-lab/start-control-plane.sh"
APPLY=0
RESTART=1

for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=1 ;;
    --no-restart) RESTART=0 ;;
    --help|-h)
      echo "Usage: $0 [--apply] [--no-restart]"
      echo "  Reads QDRANT_API_KEY from compose.local.env (gitignored)."
      echo "  Adds QDRANT_URL + QDRANT_API_KEY exports to start-control-plane.sh."
      exit 0
      ;;
  esac
done

if [[ ! -f "$ENV_FILE" ]]; then
  echo "missing env file: $ENV_FILE" >&2
  exit 1
fi
if [[ ! -f "$START" ]]; then
  echo "missing start script: $START" >&2
  exit 1
fi

KEY="$(python3 - "$ENV_FILE" <<'PY'
import sys
from pathlib import Path
path = Path(sys.argv[1])
key = ""
for line in path.read_text().splitlines():
    if line.startswith("QDRANT_API_KEY=") and not line.strip().startswith("#"):
        key = line.split("=", 1)[1].strip().strip("'").strip('"')
        break
print(key)
PY
)"

if [[ -z "$KEY" || "$KEY" == "change-me-not-for-live" ]]; then
  echo "QDRANT_API_KEY missing or placeholder in $ENV_FILE" >&2
  exit 1
fi

URL="${QDRANT_URL:-http://127.0.0.1:6333}"
echo "env_file=$ENV_FILE"
echo "start=$START"
echo "qdrant_url=$URL"
echo "qdrant_api_key=set (${#KEY} chars)"

if grep -q '^export QDRANT_API_KEY=' "$START" 2>/dev/null; then
  echo "start_script: QDRANT_API_KEY already present"
else
  echo "start_script: would add QDRANT_URL + QDRANT_API_KEY"
fi

if [[ "$APPLY" -ne 1 ]]; then
  echo "dry-run: pass --apply to update start script (and restart control plane unless --no-restart)"
  exit 0
fi

python3 - "$START" "$URL" "$KEY" <<'PY'
import sys
from pathlib import Path

start = Path(sys.argv[1])
url = sys.argv[2]
key = sys.argv[3]
text = start.read_text()
lines = text.splitlines(keepends=True)
out = []
seen_url = False
seen_key = False
for line in lines:
    if line.startswith("export QDRANT_URL="):
        out.append(f"export QDRANT_URL={url}\n")
        seen_url = True
        continue
    if line.startswith("export QDRANT_API_KEY="):
        out.append(f"export QDRANT_API_KEY={key}\n")
        seen_key = True
        continue
    out.append(line)
if not seen_url or not seen_key:
    # Insert before final cd/exec block
    insert_at = len(out)
    for i, line in enumerate(out):
        if line.startswith("cd ") or line.startswith("exec "):
            insert_at = i
            break
    block = []
    if not seen_url:
        block.append(f"export QDRANT_URL={url}\n")
    if not seen_key:
        block.append(f"export QDRANT_API_KEY={key}\n")
    out = out[:insert_at] + block + out[insert_at:]
start.write_text("".join(out))
print("updated start script (values not printed)")
PY

chmod 700 "$START"

if [[ "$RESTART" -eq 1 ]]; then
  LABEL="com.ai-lab.control-plane"
  DOMAIN="gui/$(id -u)"
  if launchctl print "${DOMAIN}/${LABEL}" >/dev/null 2>&1; then
    launchctl kickstart -k "${DOMAIN}/${LABEL}"
    echo "restarted ${LABEL}"
  else
    echo "LaunchAgent ${LABEL} not loaded; start control plane manually" >&2
  fi
fi

echo "ok"
