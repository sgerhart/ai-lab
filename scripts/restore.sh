#!/usr/bin/env bash
# Restore is destructive. It will not run without an explicit confirmation token.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONFIRM=""
BACKUP_ID=""
TARGET="${AI_LAB_BACKUP_TARGET:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --confirm-restore) CONFIRM="${2:-}"; shift ;;
    --backup-id) BACKUP_ID="${2:-}"; shift ;;
    --target) TARGET="${2:-}"; shift ;;
    *)
      echo "Usage: restore.sh --confirm-restore YES-RESTORE-LIVE --backup-id ID [--target DIR]" >&2
      exit 2
      ;;
  esac
  shift
done

if [[ "$CONFIRM" != "YES-RESTORE-LIVE" ]]; then
  echo "Refusing restore. Pass --confirm-restore YES-RESTORE-LIVE and --backup-id <id>."
  echo "Restore onto a non-live volume first. See docs/runbooks/restoring-persistent-data.md"
  exit 1
fi
if [[ -z "$BACKUP_ID" || -z "$TARGET" ]]; then
  echo "ERROR: --backup-id and --target (or AI_LAB_BACKUP_TARGET) are required" >&2
  exit 1
fi
DUMP="$TARGET/$BACKUP_ID/postgres.sql"
if [[ ! -f "$DUMP" ]]; then
  echo "ERROR: missing $DUMP" >&2
  exit 1
fi
echo "ERROR: live restore command is intentionally not wired to docker compose exec."
echo "Copy $DUMP to a throwaway Postgres, verify, then follow the runbook to replace the live volume."
echo "This script will not overwrite live data automatically."
exit 2
