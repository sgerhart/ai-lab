#!/usr/bin/env bash
# Shared helpers for host scripts. Safe: no network mutations.
set -euo pipefail

ai_lab_root() {
  local here
  here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  cd "$here/../.." && pwd
}

log() { printf '%s\n' "$*"; }
err() { printf 'ERROR: %s\n' "$*" >&2; }

require_macos() {
  if [[ "$(uname -s)" != "Darwin" ]]; then
    err "expected macOS (Darwin), found $(uname -s)"
    return 1
  fi
}

chip() {
  sysctl -n machdep.cpu.brand_string 2>/dev/null || echo unknown
}

assert_chip_contains() {
  local needle="$1"
  local actual
  actual="$(chip)"
  if [[ "$actual" != *"$needle"* ]]; then
    err "expected chip to contain '$needle', found '$actual'"
    return 1
  fi
}

# brew bundle --dry-run still needs brew. Missing brew is a preflight failure, not an install.
have() { command -v "$1" >/dev/null 2>&1; }
