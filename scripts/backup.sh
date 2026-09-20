#!/usr/bin/env bash
# Dump control-plane volumes via docker compose. Default is dry-run.
# Destination must not be the M1 data disk that holds the volumes (policy).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EXECUTE=0
TARGET="${AI_LAB_BACKUP_TARGET:-}"
COMPOSE_ENV="${COMPOSE_ENV_FILE:-$ROOT/infrastructure/compose.example.env}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --execute) EXECUTE=1 ;;
    --target) TARGET="${2:-}"; shift ;;
    --env-file) COMPOSE_ENV="${2:-}"; shift ;;
    *) echo "Usage: backup.sh [--execute] [--target DIR] [--env-file FILE]" >&2; exit 2 ;;
  esac
  shift
done

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
echo "backup id (proposed): $STAMP"
echo "target: ${TARGET:-unset}"

if [[ "$EXECUTE" -eq 0 ]]; then
  echo "dry-run: would pg_dump postgres and tar qdrant volume into \$target/$STAMP"
  echo "refusing to run docker against live systems without --execute"
  exit 0
fi

if [[ -z "$TARGET" ]]; then
  echo "ERROR: AI_LAB_BACKUP_TARGET or --target is required" >&2
  exit 1
fi
if [[ "$TARGET" == "$ROOT" ]]; then
  echo "ERROR: refusing to write backups into the git repository" >&2
  exit 1
fi

mkdir -p "$TARGET/$STAMP"
echo "NOTE: this talks to a running compose stack. Authorized --execute assumed."
docker compose -f "$ROOT/infrastructure/compose.yaml" --env-file "$COMPOSE_ENV" \
  exec -T postgres pg_dump -U "${POSTGRES_USER:-ai_lab}" "${POSTGRES_DB:-ai_lab}" \
  > "$TARGET/$STAMP/postgres.sql"
echo "wrote $TARGET/$STAMP/postgres.sql"
echo "qdrant file copy is host-specific; record volume path in the overlay before relying on this backup."
echo "RESTORE TEST REQUIRED before this backup is considered valid."
