# Known limitations

- M5 Max Ollama serves installed tags (`llama3.2:3b`, `qwen3.8:27b`, `qwen3-coder:30b`). Disk install is not RAM residency. Two large models can stay loaded together after a switch until the idle timeout or `ollama stop`.
- No real tailnet DNS suffix, IPv4, or ACL file in Git (machine names are committed: ADR 0032).
- Compose example env contains **placeholder** passwords for `docker compose config` only.
- Backup destination is iCloud Drive (ADR 0030). iCloud is sync, not a versioned backup appliance. A dump is off-box only after it has synced to another device.
- Throwaway Postgres dump→restore is tested (`scripts/test-backup-restore.sh`). Live M1 volume restore is **not** tested and `restore.sh` will not overwrite live data.
- Control-plane HTTP API **is** running on `mac-mini:8088` (Tailscale). Studio worker `:8090` is not.
- LangGraph agent loop runs inside that control plane. It is unit-tested and used for Studio chat. It is not an unattended coding factory.
- Coding Assistant cannot push, open a pull request, or run tests. Patches apply only in a harness worktree after approval. The operator has not accepted the agent screen layout (D-019).
- Git `models/catalog.json` stays `catalogued-not-pulled` even after a live `ollama pull`.
- Cloud and deep-research models stay off until `/secrets` authorizes them. There is no silent paid fallback.
- Docker container ≠ malware sandbox.
- Public GitHub remote remains a leak risk (F-002, accepted ADR 0028).
- Adjacent Clarion stack on the Air can collide on ports 5432/6379/3000 if compose is ever started **on the Air** — do not start control-plane compose on the Air.
- `datasets/` path handling: raw datasets are gitignored under `models/datasets/raw/`.
- Antares services are live; they are not installed as LaunchAgents that survive reboot.
- Vault is a compose scaffold. Secrets in use are the file store, not Vault.
