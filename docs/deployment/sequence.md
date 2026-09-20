# Deployment sequence

**Do not run this against machines without authorization.**

1. Make GitHub repo private or accept alias-only inventory (D-001).
2. Confirm `gh` identity (D-002).
3. Clone `ai-lab` onto each Mac.
4. Join each Mac to the tailnet ([../runbooks/join-tailnet.md](../runbooks/join-tailnet.md)). Fill gitignored overlays with real MagicDNS names.
5. M1: `./hosts/m1-mini/setup.sh --preflight` then `--apply` when authorized. Choose Colima vs Docker Desktop (D-013).
6. M1: copy `infrastructure/compose.example.env` to a gitignored env file; set `POSTGRES_PASSWORD` and `REDIS_PASSWORD`; keep bind `127.0.0.1` until Tailscale IP is known.
7. M1: `docker compose --env-file <file> -f infrastructure/compose.yaml up -d` **only when authorized**.
8. Verify health locally, then optionally rebind to Tailscale IP.
9. Studio: `./hosts/studio/setup.sh --preflight` then `--apply`. Do not pull models.
10. Air: `./hosts/m3-air/setup.sh --preflight` then `--apply`. Do not start always-on services.
11. Explicit `ollama pull` on Studio ([../runbooks/adding-a-model.md](../runbooks/adding-a-model.md)).
12. Platform API/worker deploy is a later authorization (Phase 4+).

Rollback: compose `down` does not delete named volumes unless `-v` is used. Never pass `-v` without a backup.
