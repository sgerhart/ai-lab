#!/usr/bin/env bash
# Non-live backup/restore proof. Starts two ephemeral Postgres containers in sequence.
# Not the M1 compose stack. Not Clarion. Uses 127.0.0.1:55433 and tmpfs.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NAME="ai-lab-pg-restore"
PORT="55433"
PASS="test-not-for-live"
DSN="postgresql://ai_lab:${PASS}@127.0.0.1:${PORT}/ai_lab"
WORKDIR="$(mktemp -d /tmp/ai-lab-restore.XXXXXX)"
STAMP="throwaway-restore-test"

if ! command -v docker >/dev/null; then
  echo "docker not available; skipping throwaway restore test"
  exit 0
fi

cleanup() {
  docker rm -f "$NAME" >/dev/null 2>&1 || true
  rm -rf "$WORKDIR"
}
trap cleanup EXIT

start_pg() {
  docker rm -f "$NAME" >/dev/null 2>&1 || true
  docker run -d --name "$NAME" \
    -e POSTGRES_USER=ai_lab \
    -e POSTGRES_PASSWORD="$PASS" \
    -e POSTGRES_DB=ai_lab \
    -e PGDATA=/var/lib/postgresql/data/pgdata \
    --tmpfs /var/lib/postgresql/data:rw,noexec,nosuid,size=256m \
    -p "127.0.0.1:${PORT}:5432" \
    postgres:16.6-alpine >/dev/null
  local ready=0
  local i
  for i in $(seq 1 60); do
    if docker exec "$NAME" pg_isready -U ai_lab -d ai_lab >/dev/null 2>&1 \
      && docker exec "$NAME" psql -U ai_lab -d ai_lab -c 'SELECT 1' >/dev/null 2>&1; then
      ready=1
      break
    fi
    sleep 1
  done
  if [[ "$ready" -ne 1 ]]; then
    echo "ephemeral Postgres on 127.0.0.1:${PORT} did not become ready" >&2
    docker logs "$NAME" >&2 || true
    exit 1
  fi
}

start_pg
docker exec -i "$NAME" psql -U ai_lab -d ai_lab >/dev/null <<'SQL'
CREATE TABLE restore_probe (id int PRIMARY KEY, note text NOT NULL);
INSERT INTO restore_probe VALUES (1, 'ai-lab throwaway restore');
SQL
mkdir -p "$WORKDIR/$STAMP"
docker exec "$NAME" pg_dump -U ai_lab ai_lab > "$WORKDIR/$STAMP/postgres.sql"
if [[ ! -s "$WORKDIR/$STAMP/postgres.sql" ]]; then
  echo "dump was empty" >&2
  exit 1
fi

docker rm -f "$NAME" >/dev/null
start_pg
"$ROOT/scripts/restore-throwaway.sh" --dump "$WORKDIR/$STAMP/postgres.sql" --container "$NAME"
NOTE="$(docker exec "$NAME" psql -U ai_lab -d ai_lab -Atc "SELECT note FROM restore_probe WHERE id = 1")"
if [[ "$NOTE" != "ai-lab throwaway restore" ]]; then
  echo "restore verification failed: got ${NOTE!r}" >&2
  exit 1
fi

echo "throwaway backup/restore OK (row survived dump → new container → restore)"
echo "This does not prove live M1 volume restore. Destination policy is iCloud (ADR 0030); live restore remains untested."
