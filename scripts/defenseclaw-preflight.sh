#!/usr/bin/env bash
# Read-only DefenseClaw status for the Air operator plane (FEAT-014 / IWO-044).
# Never runs `setup`, never writes config. Pass --apply is rejected on purpose.
set -euo pipefail
export PATH="${HOME}/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

for arg in "$@"; do
  case "$arg" in
    --apply)
      echo "refusing --apply: use a separate authorized IWO for defenseclaw setup" >&2
      exit 2
      ;;
    --help|-h)
      cat <<'EOF'
Usage: ./scripts/defenseclaw-preflight.sh

Read-only checks:
  - defenseclaw on PATH
  - ~/.defenseclaw present
  - version / status summaries (no secrets)
  - whether ~/.cursor/hooks.json exists

Does NOT run: defenseclaw setup, gateway restart, MCP allow/deny.
EOF
      exit 0
      ;;
  esac
done

ok=1
if ! command -v defenseclaw >/dev/null 2>&1; then
  echo "defenseclaw: NOT FOUND on PATH"
  ok=0
else
  echo "defenseclaw: $(command -v defenseclaw)"
  defenseclaw version 2>/dev/null | sed 's/^/  /' || true
fi

DATA="${HOME}/.defenseclaw"
if [[ ! -d "$DATA" ]]; then
  echo "data dir: missing ($DATA)"
  ok=0
else
  echo "data dir: $DATA"
  if [[ -f "$DATA/config.yaml" ]]; then
    # Print only non-secret summary fields via python if available
    python3 - <<'PY' 2>/dev/null || echo "  (could not summarize config.yaml)"
from pathlib import Path
try:
    import yaml
except ImportError:
    print("  config.yaml present (PyYAML not installed; skip parse)")
    raise SystemExit(0)
cfg = yaml.safe_load(Path.home().joinpath(".defenseclaw/config.yaml").read_text()) or {}
claw = cfg.get("claw") or {}
gr = cfg.get("guardrail") or {}
print(f"  claw.mode: {claw.get('mode')}")
print(f"  guardrail.connector: {gr.get('connector')}")
print(f"  guardrail.mode: {gr.get('mode')}")
print(f"  guardrail.enabled: {gr.get('enabled')}")
print(f"  hook_fail_mode: {gr.get('hook_fail_mode')}")
PY
  fi
fi

if [[ -f "${HOME}/.cursor/hooks.json" ]]; then
  echo "cursor hooks: present (~/.cursor/hooks.json)"
else
  echo "cursor hooks: ABSENT (IWO-045 when authorized: defenseclaw setup cursor → Add)"
fi

if command -v defenseclaw >/dev/null 2>&1; then
  echo "--- status (truncated) ---"
  defenseclaw status 2>/dev/null | head -n 40 | sed 's/^/  /' || true
fi

echo "---"
echo "next (NOT run by this script):"
echo "  defenseclaw setup cursor   # choose Add to keep Antigravity; needs explicit auth"
echo "  ./scripts/lab-mcp-server.sh  # lab MCP for IDEs (FEAT-005); scan before trust"

if [[ "$ok" -ne 1 ]]; then
  exit 1
fi
echo "preflight: ok (read-only)"
