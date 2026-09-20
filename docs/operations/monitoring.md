# Monitoring

**Status:** Planned. No observability stack is in the default compose file (M1 memory).

Phase 2 health is:

- `docker compose ps` + healthchecks
- `./scripts/health-check.sh` (repo-local; `--live` is opt-in and **not** run by CI)
- Postgres `pg_isready` via compose healthcheck
- Ollama `/api/tags` on Studio when deployed

Optional compose profile `observability` is a stub README, not a second Prometheus stack. Do not enable it until D-010 is decided and RAM is measured.

Agent jobs store status in Postgres; that is the first "dashboard". A UI on the Air can wait.
