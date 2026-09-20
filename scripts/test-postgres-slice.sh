#!/usr/bin/env bash
# Ephemeral Postgres on loopback for checkpoint tests. Not an M1 deploy.
# Starts postgres:16.6-alpine on 127.0.0.1:55432, runs tests, removes the container.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NAME="ai-lab-pg-test"
PORT="55432"
PASS="test-not-for-live"
export DATABASE_URL="postgresql://ai_lab:${PASS}@127.0.0.1:${PORT}/ai_lab"

if ! command -v docker >/dev/null; then
  echo "docker not available; skipping postgres slice tests"
  exit 0
fi

cleanup() {
  docker rm -f "$NAME" >/dev/null 2>&1 || true
}
trap cleanup EXIT

docker rm -f "$NAME" >/dev/null 2>&1 || true
# tmpfs: this Air's Docker VM is often full (Clarion). Do not prune that stack.
docker run -d --name "$NAME" \
  -e POSTGRES_USER=ai_lab \
  -e POSTGRES_PASSWORD="$PASS" \
  -e POSTGRES_DB=ai_lab \
  -e PGDATA=/var/lib/postgresql/data/pgdata \
  --tmpfs /var/lib/postgresql/data:rw,noexec,nosuid,size=256m \
  -p "127.0.0.1:${PORT}:5432" \
  postgres:16.6-alpine >/dev/null

PYTHON="${ROOT}/platform/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON="python3"
fi

ready=0
for _ in $(seq 1 60); do
  if "$PYTHON" -c "import psycopg; psycopg.connect('$DATABASE_URL').close()" >/dev/null 2>&1; then
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

export PYTHONPATH="$ROOT/platform/src"
"$PYTHON" -m unittest tests.test_postgres_slice -v
echo "postgres slice tests OK (ephemeral container removed on exit)"
