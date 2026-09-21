#!/usr/bin/env bash
# Compose CLI: plugin first, then docker-compose. Sourced, not executed.

ai_lab_compose() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    docker compose "$@"
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose "$@"
  else
    echo "ERROR: docker compose / docker-compose not found" >&2
    return 1
  fi
}
