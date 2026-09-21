# Backup and recovery policy

- Source of truth to back up: Postgres volume, Qdrant volume, optional artifact directory on the M1.
- Redis: optional; rebuild from Postgres.
- Studio weights: large; backup separately or treat as rebuildable via `ollama pull` plus a checked catalog.
- Destination: **iCloud Drive** (ADR 0030), default `~/Library/Mobile Documents/com~apple~CloudDocs/ai-lab-backups`. Not the git repo. Not “only the M1 SSD”.
- A backup is not valid until a restore test has been performed onto a non-live target. `scripts/test-backup-restore.sh` is that throwaway proof. It does **not** prove M1 live restore.
- `scripts/restore.sh` requires `--confirm-restore` and a backup id. It will not overwrite live volumes even then.

See runbooks: [../runbooks/backing-up-persistent-data.md](../runbooks/backing-up-persistent-data.md), [../runbooks/restoring-persistent-data.md](../runbooks/restoring-persistent-data.md).
