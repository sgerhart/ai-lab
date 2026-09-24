#!/usr/bin/env bash
# Rotate mini control-plane API token + Postgres password (F-012).
# Default is dry-run. Does not print secret values to the terminal.
#
# Usage (from Air with SSH to mac-mini):
#   ./scripts/rotate-control-plane-secrets.sh           # dry-run
#   ./scripts/rotate-control-plane-secrets.sh --apply  # live rotate + restart
#
# Host mutate requires explicit --apply (AGENTS.md).

set -euo pipefail

APPLY=0
MINI_HOST="${AI_LAB_MINI_SSH:-mac-mini}"

usage() {
  echo "Usage: $0 [--apply] [--host HOST]" >&2
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply) APPLY=1; shift ;;
    --host) MINI_HOST="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) usage ;;
  esac
done

log() { printf '%s\n' "$*"; }

log "host=$MINI_HOST apply=$APPLY"
log "Rotates AI_LAB_API_TOKEN and Postgres password on the mini (F-012)."
log "Secret values are never printed here. Paste the new token into Air after --apply."

if [[ "$APPLY" != "1" ]]; then
  log "dry-run only. Re-run with --apply to mutate the mini."
  log "Planned steps:"
  log "  1) Generate new API token + DB password (openssl rand)"
  log "  2) Rewrite ~/.ai-lab/start-control-plane.sh (token + DATABASE_URL)"
  log "  3) Update infrastructure/compose.local.env POSTGRES_PASSWORD (gitignored)"
  log "  4) Store new token at ~/.ai-lab/api-token.rotated (mode 600)"
  log "  5) Recreate postgres; restart control plane"
  exit 0
fi

ssh -o BatchMode=yes "$MINI_HOST" 'bash -s' <<'EOF'
set -euo pipefail
export PATH="/opt/homebrew/bin:$PATH"

REPO="${HOME}/workspace/github/sgerhart/ai-lab"
START="${HOME}/.ai-lab/start-control-plane.sh"
COMPOSE_ENV="${REPO}/infrastructure/compose.local.env"
MARKER="${HOME}/.ai-lab/rotation-f012.marker"
TOKEN_OUT="${HOME}/.ai-lab/api-token.rotated"

[[ -f "$START" ]] || { echo "missing start script"; exit 1; }
[[ -d "$REPO" ]] || { echo "missing repo"; exit 1; }

export NEW_TOKEN NEW_DB_PASS
NEW_TOKEN="$(openssl rand -hex 32)"
NEW_DB_PASS="$(openssl rand -hex 24)"

python3 - <<'PY'
from pathlib import Path
import os, re, urllib.parse

token = os.environ["NEW_TOKEN"]
dbpass = os.environ["NEW_DB_PASS"]
start = Path.home() / ".ai-lab" / "start-control-plane.sh"
text = start.read_text()

def repl_env(name: str, value: str, src: str) -> str:
    pat = re.compile(rf"^(export\s+{re.escape(name)}=).*$\n?", re.M)
    line = f"export {name}={value}\n"
    if pat.search(src):
        return pat.sub(line, src, count=1)
    return src + ("\n" if not src.endswith("\n") else "") + line

text = repl_env("AI_LAB_API_TOKEN", token, text)

pat = re.compile(r'^(export\s+DATABASE_URL=["\']?)([^"\'\n]+)(["\']?\s*)$', re.M)
m = pat.search(text)
if not m:
    raise SystemExit("DATABASE_URL not found in start script")
url = m.group(2)
scheme, rest = url.split("://", 1)
creds, hostpart = rest.split("@", 1)
if ":" not in creds:
    raise SystemExit("DATABASE_URL missing user:pass")
user, _old = creds.split(":", 1)
new_url = f"{scheme}://{user}:{urllib.parse.quote(dbpass, safe='')}@{hostpart}"
text = pat.sub(lambda mm: f"{mm.group(1)}{new_url}{mm.group(3)}", text, count=1)
start.write_text(text)
os.chmod(start, 0o700)
print("start_script_updated")

compose = Path.home() / "workspace/github/sgerhart/ai-lab/infrastructure/compose.local.env"
if compose.is_file():
    c = compose.read_text()
    c2 = re.sub(r"^POSTGRES_PASSWORD=.*$", f"POSTGRES_PASSWORD={dbpass}", c, count=1, flags=re.M)
    if c2 == c:
        c2 = c.rstrip() + f"\nPOSTGRES_PASSWORD={dbpass}\n"
    compose.write_text(c2)
    os.chmod(compose, 0o600)
    print("compose_local_env_updated")
else:
    print("compose_local_env_missing")

hint = Path.home() / ".ai-lab" / "api-token.rotated"
hint.write_text(token + "\n")
os.chmod(hint, 0o600)
print("token_file_written")
PY

cd "$REPO"
if [[ -f "$COMPOSE_ENV" ]]; then
  if command -v docker >/dev/null 2>&1; then
    docker compose -f infrastructure/compose.yaml \
      -f infrastructure/compose.tailscale.local.yaml \
      --env-file infrastructure/compose.local.env \
      up -d --force-recreate --no-deps postgres
    echo "postgres_recreated"
  else
    echo "docker_missing_skip_postgres"
  fi
fi

pid=$(pgrep -f 'uvicorn --factory ai_lab_platform.control_app:app_factory' | head -1 || true)
if [[ -n "${pid:-}" ]]; then
  kill "$pid" || true
  sleep 1
  kill -9 "$pid" 2>/dev/null || true
  echo "stopped_api=$pid"
fi
nohup "$HOME/.ai-lab/start-control-plane.sh" >> "$HOME/.ai-lab/control-plane.log" 2>&1 &
echo $! > "$HOME/.ai-lab/control-plane.pid"
ok=0
for i in $(seq 1 40); do
  if curl -sf --max-time 2 "http://127.0.0.1:8088/health" >/dev/null 2>&1 \
     || curl -sf --max-time 2 "http://100.80.117.123:8088/health" >/dev/null 2>&1; then
    ok=1
    break
  fi
  sleep 0.4
done
[[ "$ok" == 1 ]] || { echo "health_fail"; tail -20 "$HOME/.ai-lab/control-plane.log"; exit 1; }
date -u +"rotated_at=%Y-%m-%dT%H:%M:%SZ" > "$MARKER"
echo "control_plane_restarted"
echo "DONE — on mini read: $TOKEN_OUT (mode 600; never commit)"
EOF
