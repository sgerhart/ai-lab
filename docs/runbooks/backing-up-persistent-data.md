# Backing up persistent data

**Prerequisites:** Compose running (when deployed). Destination is **iCloud Drive** (ADR 0030).

**Effects:** Writes `postgres.sql` under a timestamp directory in iCloud Drive (`~/Library/Mobile Documents/com~apple~CloudDocs/ai-lab-backups` unless `AI_LAB_BACKUP_TARGET` is set).

**Steps:** `./scripts/backup.sh` (dry-run). Then `--execute` when authorized. Confirm the file appears on another Apple device before treating it as off-box.

**Verify:** File non-empty. Throwaway restore: `./scripts/test-backup-restore.sh`. **A dump is invalid as a live backup until iCloud has synced and a restore onto a non-live database succeeds. Live M1 restore is still untested.**

**Rollback:** Delete the timestamp directory if the dump is bad.
