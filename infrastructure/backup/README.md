# Backup layout

`scripts/backup.sh` writes timestamped directories under iCloud Drive by default (ADR 0030): `~/Library/Mobile Documents/com~apple~CloudDocs/ai-lab-backups`. Override with `AI_LAB_BACKUP_TARGET` (must stay under CloudDocs unless `--allow-other-target`). Do not write dumps into Git.

Restore: `scripts/restore.sh` — refuses without `--confirm-restore`, and still will not overwrite live volumes. Throwaway proof: `scripts/test-backup-restore.sh`.
