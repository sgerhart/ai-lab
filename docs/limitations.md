# Known limitations

- M5 Max Ollama/MLX compatibility is **unverified**.
- No real tailnet DNS suffix, IPv4, or ACL file in Git (machine names are committed: ADR 0032).
- Compose example env contains **placeholder** passwords for `docker compose config` only.
- Backup destination is iCloud Drive (ADR 0030). iCloud is sync, not a versioned backup appliance. A dump is off-box only after it has synced to another device.
- Throwaway Postgres dump→restore is tested (`scripts/test-backup-restore.sh`). Live M1 volume restore is **not** tested and `restore.sh` will not overwrite live data.
- Agent HTTP API is not a running service on lab hosts.
- LangGraph vertical slice is unit-tested; it is not a live control-plane process.
- Docker container ≠ malware sandbox.
- Public GitHub remote remains a leak risk (F-002, accepted ADR 0028).
- Adjacent Clarion stack on the Air can collide on ports 5432/6379/3000 if compose is ever started **on the Air** — do not start control-plane compose on the Air.
- `datasets/` path handling: raw datasets are gitignored under `models/datasets/raw/`.
