#!/usr/bin/env bash
# Restore a Postgres dump onto a throwaway database. Never targets compose/live volumes.
#
# Use --container NAME where NAME is an ephemeral ai-lab-pg-* container
# (see scripts/test-backup-restore.sh). Loopback DSN without a container is
# accepted only as a guard check; applying SQL requires docker exec psql so
# COPY dumps work.
set -euo pipefail
DUMP=""
DSN=""
CONTAINER=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dump) DUMP="${2:-}"; shift ;;
    --dsn) DSN="${2:-}"; shift ;;
    --container) CONTAINER="${2:-}"; shift ;;
    *)
      echo "Usage: restore-throwaway.sh --dump FILE --container ai-lab-pg-NAME" >&2
      echo "       restore-throwaway.sh --dump FILE --dsn postgresql://...@127.0.0.1:5543x/..." >&2
      exit 2
      ;;
  esac
  shift
done

if [[ -z "$DUMP" ]]; then
  echo "ERROR: --dump is required" >&2
  exit 1
fi
if [[ ! -f "$DUMP" ]]; then
  echo "ERROR: dump not found: $DUMP" >&2
  exit 1
fi

if [[ -n "$DSN" ]]; then
  if [[ "$DSN" != *127.0.0.1* && "$DSN" != *localhost* && "$DSN" != *::1* ]]; then
    echo "ERROR: throwaway restore only accepts a loopback DSN" >&2
    exit 1
  fi
  if [[ "$DSN" == *5432* && "$DSN" != *5543* ]]; then
    echo "ERROR: refusing port 5432 (live/Clarion collision). Use an ephemeral port such as 55433." >&2
    exit 1
  fi
fi

if [[ -z "$CONTAINER" ]]; then
  if [[ -n "$DSN" ]]; then
    echo "ERROR: DSN accepted as loopback, but apply requires --container ai-lab-pg-* (psql COPY)." >&2
    exit 1
  fi
  echo "ERROR: --container is required to apply a dump" >&2
  exit 1
fi

if [[ "$CONTAINER" != ai-lab-pg-* ]]; then
  echo "ERROR: refusing container '$CONTAINER'; must be ephemeral name ai-lab-pg-*" >&2
  exit 1
fi

docker exec -i "$CONTAINER" psql -U ai_lab -d ai_lab < "$DUMP" >/dev/null
echo "restored $DUMP into throwaway container $CONTAINER"
