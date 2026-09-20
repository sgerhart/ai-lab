# Start and stop control-plane services

**Prerequisites:** M1 setup applied, compose env with real passwords, human authorization.

**Effects:** Starts or stops Postgres, Redis, Qdrant. Data remains in named volumes unless `-v` is used.

**Start:** `docker compose -f infrastructure/compose.yaml --env-file <gitignored env> up -d`

**Stop:** `docker compose ... stop` (preferred) or `down` without `-v`.

**Verify:** `docker compose ps`, healthchecks healthy. From the M1: `nc -vz 127.0.0.1 5432`.

**Rollback:** `down` without `-v`. Never `down -v` without a tested backup.
