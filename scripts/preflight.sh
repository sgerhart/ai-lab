#!/usr/bin/env bash
# Repository and local-tool preflight. Does not install packages or start compose.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=lib/common.sh
source "$ROOT/scripts/lib/common.sh"
cd "$ROOT"

log "== ai-lab preflight =="
git rev-parse --show-toplevel
log "python3: $(python3 --version 2>/dev/null || echo missing)"
have uv && log "uv: $(uv --version)" || log "uv: missing (ok until host apply)"
have docker && log "docker: $(docker --version | head -1)" || log "docker: missing"
have brew && log "brew: present" || log "brew: missing"

"$ROOT/scripts/validate-repo.sh"
python3 -m unittest discover -s "$ROOT/tests" -v

if have docker && docker compose version >/dev/null 2>&1; then
  docker compose -f "$ROOT/infrastructure/compose.yaml" --env-file "$ROOT/infrastructure/compose.example.env" config >/dev/null
  log "compose config: OK"
else
  log "compose config: skipped (docker compose not available)"
fi

log "preflight complete (no host changes)"
