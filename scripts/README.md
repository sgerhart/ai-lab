# Scripts

All host-mutating scripts default to checks. `--apply` / `--live` / `--confirm-restore` are explicit.

| Script | Mutates hosts? |
|--------|----------------|
| [preflight.sh](preflight.sh) | No |
| [validate-repo.sh](validate-repo.sh) | No |
| [host-setup.sh](host-setup.sh) | Only with `--apply` |
| [bootstrap.sh](bootstrap.sh) | Only with `--apply` |
| [health-check.sh](health-check.sh) | No (`--live` probes, does not write) |
| [backup.sh](backup.sh) | Writes iCloud Drive backup dir only with `--execute` (ADR 0030) |
| [restore.sh](restore.sh) | Only with `--confirm-restore <id>` — and even then it **refuses** to overwrite live volumes |
| [restore-throwaway.sh](restore-throwaway.sh) | Restores a dump into an ephemeral `ai-lab-pg-*` container only |
| [test-backup-restore.sh](test-backup-restore.sh) | Ephemeral dump→restore on `127.0.0.1:55433` (tmpfs); not M1 |
| [platform.sh](platform.sh) | No (local harness CLI / loopback serve) |
| [control-plane.sh](control-plane.sh) | No (loopback uvicorn; refuses non-loopback) |
| [studio-worker.sh](studio-worker.sh) | No (loopback uvicorn; refuses non-loopback) |
| [test-postgres-slice.sh](test-postgres-slice.sh) | Starts an ephemeral loopback Postgres (`127.0.0.1:55432`, data on tmpfs) for checkpoint tests, then removes it |
| [eval-dry-run.sh](eval-dry-run.sh) | No (FakeBackend smoke; `--pull` exits 2) |
| [train.sh](train.sh) | No (always refuses) |
