#!/usr/bin/env bash
# Dump control-plane volumes via docker compose. Default is dry-run.
# Destination: iCloud Drive (ADR 0030), not the git repo and not the M1 data volume alone.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=lib/compose.sh
source "$ROOT/scripts/lib/compose.sh"
EXECUTE=0
ALLOW_OTHER=0
ICLOUD_DRIVE="${HOME}/Library/Mobile Documents/com~apple~CloudDocs"
DEFAULT_TARGET="${ICLOUD_DRIVE}/ai-lab-backups"
TARGET="${AI_LAB_BACKUP_TARGET:-}"
COMPOSE_ENV="${COMPOSE_ENV_FILE:-$ROOT/infrastructure/compose.example.env}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --execute) EXECUTE=1 ;;
    --target) TARGET="${2:-}"; shift ;;
    --env-file) COMPOSE_ENV="${2:-}"; shift ;;
    --allow-other-target) ALLOW_OTHER=1 ;;
    *) echo "Usage: backup.sh [--execute] [--target DIR] [--env-file FILE] [--allow-other-target]" >&2; exit 2 ;;
  esac
  shift
done

if [[ -z "$TARGET" ]]; then
  TARGET="$DEFAULT_TARGET"
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
echo "backup id (proposed): $STAMP"
echo "target: $TARGET"
echo "policy: iCloud Drive (ADR 0030); dumps must not enter Git"

if [[ "$EXECUTE" -eq 0 ]]; then
  echo "dry-run: would pg_dump postgres into $TARGET/$STAMP/postgres.sql"
  echo "refusing to run docker against live systems without --execute"
  exit 0
fi

if [[ "$TARGET" == "$ROOT" || "$TARGET" == "$ROOT"/* ]]; then
  echo "ERROR: refusing to write backups into the git repository" >&2
  exit 1
fi

under_icloud=0
if [[ "$TARGET" == "$ICLOUD_DRIVE" || "$TARGET" == "$ICLOUD_DRIVE"/* ]]; then
  under_icloud=1
fi
if [[ "$under_icloud" -eq 0 && "$ALLOW_OTHER" -eq 0 ]]; then
  echo "ERROR: target is not under iCloud Drive ($ICLOUD_DRIVE)." >&2
  echo "Pass --allow-other-target only for a later ADR destination." >&2
  exit 1
fi

mkdir -p "$TARGET/$STAMP"
echo "NOTE: this talks to a running compose stack. Authorized --execute assumed."
ai_lab_compose -f "$ROOT/infrastructure/compose.yaml" --env-file "$COMPOSE_ENV" \
  exec -T postgres pg_dump -U "${POSTGRES_USER:-ai_lab}" "${POSTGRES_DB:-ai_lab}" \
  < /dev/null > "$TARGET/$STAMP/postgres.sql"
echo "wrote $TARGET/$STAMP/postgres.sql"
echo "iCloud must finish syncing before this dump counts as off-box."
echo "qdrant file copy is host-specific; record volume path in the overlay before relying on this backup."
echo "RESTORE TEST REQUIRED before this backup is considered valid."
