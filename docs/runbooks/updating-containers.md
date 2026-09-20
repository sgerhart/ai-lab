# Updating containers

**Prerequisites:** M1 compose running or not. Human authorization.

**Effects:** New image tags, possible downtime.

**Steps:** Edit pins in `infrastructure/compose.yaml`. `docker compose pull`. Recreate with `up -d`. Do not use `:latest`.

**Verify:** `docker compose ps`, healthchecks, `pg_isready` equivalent.

**Rollback:** Revert the tag in Git and pull the previous image.
