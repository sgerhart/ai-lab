# Known limitations

- M5 Max Ollama/MLX compatibility is **unverified**.
- M3 unified memory is **unattested**.
- No real tailnet names, IPs, or ACLs in Git.
- Compose example env contains **placeholder** passwords for `docker compose config` only.
- Backup destination is undecided; therefore backups cannot be declared working.
- Restore has not been tested against real volumes.
- Agent HTTP API is not a running service.
- LangGraph is not integrated.
- Docker container ≠ malware sandbox.
- Public GitHub remote remains a leak risk (F-002).
- Adjacent Clarion stack on the Air can collide on ports 5432/6379/3000 if compose is ever started **on the Air** — do not start control-plane compose on the Air.
- `datasets/` path handling: raw datasets are gitignored under `models/datasets/raw/`.
