# Monitoring

**Status:** Deferred (ADR 0026). No observability stack is in the default compose file (M1 memory).

Phase 2 health is:

- `docker compose ps` + healthchecks
- `./scripts/health-check.sh` (repo-local; `--live` is opt-in and **not** run by CI)
- Postgres `pg_isready` via compose healthcheck
- Ollama `/api/tags` on Studio when deployed

Optional compose profile `observability` is a README only. Do not enable it until a new ADR names tools and RAM is measured on a running M1.

Agent jobs store status in Postgres; that is the first "dashboard". A UI on the Air can wait.
