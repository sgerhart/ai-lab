#!/usr/bin/env bash
# Generic host setup. Invoked by hosts/<role>/setup.sh
# Default --preflight. Never pulls models. Never changes SSH/firewall.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=lib/common.sh
source "$ROOT/scripts/lib/common.sh"

ROLE=""
MODE="preflight"
FORCE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host) ROLE="${2:-}"; shift ;;
    --preflight) MODE=preflight ;;
    --dry-run) MODE=dry-run ;;
    --apply) MODE=apply ;;
    --force) FORCE=1 ;;
    -h|--help)
      echo "Usage: host-setup.sh --host {m1-mini|studio|m3-air} [--preflight|--dry-run|--apply] [--force]"
      exit 0
      ;;
    *) err "unknown argument: $1"; exit 2 ;;
  esac
  shift
done

if [[ -z "$ROLE" ]]; then
  err "missing --host"
  exit 2
fi

HOST_DIR="$ROOT/hosts/$ROLE"
BREWFILE="$HOST_DIR/Brewfile"

EXPECTED_CHIP=""
case "$ROLE" in
  m1-mini) EXPECTED_CHIP="M1" ;;
  studio) EXPECTED_CHIP="M5" ;;
  m3-air) EXPECTED_CHIP="M3" ;;
  *) err "unknown host: $ROLE"; exit 2 ;;
esac

log "host role: $ROLE"
log "mode: $MODE"
require_macos
log "chip: $(chip)"

chip_ok=1
if ! assert_chip_contains "$EXPECTED_CHIP"; then
  chip_ok=0
fi
if [[ "$chip_ok" -eq 0 ]]; then
  if [[ "$FORCE" -eq 1 ]]; then
    log "continuing because --force was set"
  elif [[ "$MODE" == "apply" ]]; then
    err "refusing --apply on unexpected chip (use --force if intentional)"
    exit 1
  else
    log "warning: chip mismatch (expected when running this script on a different Mac)"
  fi
fi

if ! have brew; then
  err "Homebrew not found. Install Homebrew yourself; this script will not pipe curl to bash."
  exit 1
fi

if [[ ! -f "$BREWFILE" ]]; then
  err "missing $BREWFILE"
  exit 1
fi

case "$MODE" in
  preflight)
    log "preflight: brew and Brewfile OK; no packages will be installed"
    have docker && log "docker: $(docker --version 2>/dev/null | head -1)" || log "docker: not installed (ok until apply on m1-mini)"
    have uv && log "uv: $(uv --version 2>/dev/null)" || log "uv: not installed"
    have ollama && log "ollama: present" || log "ollama: not installed"
    have tailscale && log "tailscale: present" || log "tailscale: not installed"
    log "preflight complete"
    ;;
  dry-run)
    log "dry-run: brew bundle check --file=$BREWFILE (Homebrew 6 has no --dry-run)"
    if brew bundle check --file="$BREWFILE" --verbose; then
      log "brew bundle check: all Brewfile deps already installed"
    else
      log "brew bundle check: missing formulae (expected before first apply)"
    fi
    ;;
  apply)
    log "APPLY: brew bundle install --file=$BREWFILE"
    brew bundle install --file="$BREWFILE"
    if [[ "$ROLE" == "studio" ]]; then
      log "note: not pulling any Ollama models"
    fi
    log "apply complete"
    ;;
esac
