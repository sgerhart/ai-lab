# Deployment sequence

**Do not run this against machines without authorization.**

1. GitHub stays public (ADR 0028). Keep alias-only inventory (ADR 0005).
2. Confirm `gh` identity (ADR 0022).
3. Clone `ai-lab` onto each Mac at `~/workspace/github/sgerhart/ai-lab` (ADR 0035).
4. Join each Mac to the tailnet ([../runbooks/join-tailnet.md](../runbooks/join-tailnet.md)). Set machine names `mac-mini`, `mac-studio`, `mac-air`. Fill gitignored overlays with IPv4 and the tailnet suffix.
5. M1: `./hosts/m1-mini/setup.sh --preflight` then `--apply` when authorized. Engine is Colima (ADR 0023).
6. M1: copy `infrastructure/compose.example.env` to a gitignored env file; set `POSTGRES_PASSWORD`, `REDIS_PASSWORD`, and `QDRANT_API_KEY`; keep bind `127.0.0.1` until Tailscale IP is known.
7. M1: `docker compose --env-file <file> -f infrastructure/compose.yaml up -d` **only when authorized**.
8. Verify health locally, then optionally rebind to Tailscale IP.
9. Studio: `./hosts/studio/setup.sh --preflight` then `--apply`. Do not pull models. Do not require Thunderbolt NVMe (ADR 0033).
10. Air: `./hosts/m3-air/setup.sh --preflight` then `--apply`. Do not start always-on services. Air Ollama `*:11434` is accepted (ADR 0029).
11. Explicit `ollama pull` on Studio ([../runbooks/adding-a-model.md](../runbooks/adding-a-model.md)).
12. First authorized backup: `./scripts/backup.sh --execute` to iCloud Drive (ADR 0030). Confirm the dump on another Apple device. Throwaway restore is already tested; live M1 restore is not.
13. Platform API/worker deploy is a later authorization (Phase 4+).

Rollback: compose `down` does not delete named volumes unless `-v` is used. Never pass `-v` without a backup.
