# Backing up persistent data

**Prerequisites:** Compose running (when deployed), `AI_LAB_BACKUP_TARGET` **not** the M1 volume disk. D-011 open until destination exists.

**Effects:** Writes `postgres.sql` under a timestamp directory.

**Steps:** `./scripts/backup.sh` (dry-run). Then `--execute --target ...` when authorized.

**Verify:** File non-empty. Throwaway restore: `./scripts/test-backup-restore.sh`. **A backup is invalid until that class of restore succeeds. Live M1 restore is still untested (D-011).**

**Rollback:** Delete the timestamp directory if the dump is bad.
