# Backup layout

`scripts/backup.sh` writes timestamped directories. Destination is `AI_LAB_BACKUP_TARGET` (must not be the M1 disk that holds the volumes).

Restore: `scripts/restore.sh` — refuses without `--confirm-restore`.
