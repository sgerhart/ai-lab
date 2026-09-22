# Control plane (M1 Mac mini)

**Host directory:** [`hosts/m1-mini/`](../../hosts/m1-mini/README.md)  
**Status:** Compose + FastAPI/LangGraph **live** on `mac-mini` (Tailscale, 2026-09-21). Studio worker **not** deployed. Live restore **untested**.

## Why this host

16 GB unified memory, expected to stay powered. If the Studio reboots mid-job, work orders must still exist.

## Runs here

| Component | Why | Default compose |
|-----------|-----|-----------------|
| PostgreSQL | Authoritative work orders, audit, approvals | Yes |
| Redis | Queue and cache only | Yes |
| Qdrant | Vector memory | Yes |
| Agent API / orchestrator / scheduler | Platform processes | **Live** on mini (`:8088`, LaunchAgent); Studio dispatch pending |
| Backup orchestration | Scripts in `scripts/` and `infrastructure/backup/` | Scripts only |
| Monitoring | Optional profile `observability` | Off |

Does **not** run large local models.

## Memory budget (planning numbers, not measurements)

These are conservative *targets* so the 16 GB Mac is not packed:

| Consumer | Target |
|----------|--------|
| macOS + always-on apps | ~6–8 GB |
| Colima/Docker VM cap | 3 GB suggested |
| postgres container | 512 MB limit |
| qdrant container | 512 MB limit |
| redis container | 128 MB limit |
| Headroom | remainder |

Do not enable the observability profile until this budget is measured on the real mini.

## Failure behavior

- Studio down: new jobs that need inference stay `queued` or fail with a visible error after timeout. They do not vanish.
- M1 reboot: Postgres volume is the record. Redis may be empty. Orchestrator reconciles `running` → retry or `failed` per policy.
- Tailscale down: local compose on loopback still works on the mini; other hosts cannot reach it.

## Bind address

`AI_LAB_BIND_ADDRESS` defaults to `127.0.0.1`. Other tailnet nodes cannot use that. Setting it to the mini's Tailscale IPv4 is a **deploy-time** step documented in [../runbooks/start-stop-control-plane.md](../runbooks/start-stop-control-plane.md).
