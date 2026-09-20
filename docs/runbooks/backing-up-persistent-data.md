# Backing up persistent data

**Prerequisites:** Compose running (when deployed), `AI_LAB_BACKUP_TARGET` **not** the M1 volume disk. D-011 open until destination exists.

**Effects:** Writes `postgres.sql` under a timestamp directory.

**Steps:** `./scripts/backup.sh` (dry-run). Then `--execute --target ...` when authorized.

**Verify:** File non-empty. **A backup is invalid until a restore test onto a non-live database succeeds.**

**Rollback:** Delete the timestamp directory if the dump is bad.
