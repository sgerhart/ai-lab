# PostgreSQL

Init scripts in `init/` run only on an empty data volume.

The platform schema is applied by `platform/src/ai_lab_platform/schema.sql` (idempotent) when the harness starts, or manually:

```bash
# Not authorized to run against live hosts from this agent session.
# docker compose exec -T postgres psql -U ai_lab -d ai_lab < platform/src/ai_lab_platform/schema.sql
```
