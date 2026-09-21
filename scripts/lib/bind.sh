#!/usr/bin/env bash
# Bind policy: loopback, or this host's Tailscale IPv4. Never 0.0.0.0.
# Sourced by control-plane.sh / studio-worker.sh. Do not execute.

ai_lab_bind_allowed() {
  local host="${1:-}"
  case "$host" in
    ""|0.0.0.0|::|\[::\]) return 1 ;;
    127.0.0.1|localhost|::1) return 0 ;;
  esac
  if command -v tailscale >/dev/null 2>&1; then
    local ts
    ts="$(tailscale ip -4 2>/dev/null | head -1 || true)"
    if [[ -n "$ts" && "$host" == "$ts" ]]; then
      return 0
    fi
  fi
  return 1
}
