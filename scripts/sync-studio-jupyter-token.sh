#!/usr/bin/env bash
# Copy Studio Jupyter token onto the mini (gitignored path). Run from Air with SSH to both.
# Usage: ./scripts/sync-studio-jupyter-token.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=lib/common.sh
source "$ROOT/scripts/lib/common.sh"

STUDIO_HOST="${AI_LAB_STUDIO_SSH:-mac-studio}"
MINI_HOST="${AI_LAB_MINI_SSH:-mac-mini}"
DEST='~/.ai-lab/studio-jupyter.token'

log "reading token from ${STUDIO_HOST}"
TOKEN="$(ssh -o BatchMode=yes "$STUDIO_HOST" 'cat ~/.ai-lab/jupyter/token')"
[[ -n "$TOKEN" ]] || { err "empty token"; exit 1; }

log "writing ${DEST} on ${MINI_HOST} (mode 600)"
ssh -o BatchMode=yes "$MINI_HOST" "mkdir -p ~/.ai-lab && umask 077 && printf '%s\n' '$TOKEN' > ~/.ai-lab/studio-jupyter.token && chmod 600 ~/.ai-lab/studio-jupyter.token && echo ok"
log "done — set STUDIO_JUPYTER_URL=http://mac-studio:8888 on the mini LaunchAgent/env"
