# Control plane (M1 Mac mini)

**Host directory:** [`hosts/m1-mini/`](../../hosts/m1-mini/README.md)  
**Status:** Compose + FastAPI/LangGraph **live** on `mac-mini` (Tailscale).
Personal Agent Studio, Qdrant-backed memory, and minute scheduler tick **live**
(2026-09-24). Studio worker dispatch still optional. Live restore **untested**.

## Why this host

16 GB unified memory, expected to stay powered. If the Studio reboots mid-job,
work orders and agent definitions must still exist.

## Runs here

| Component | Why | Live |
|-----------|-----|------|
| PostgreSQL | Work orders, audit, approvals, checkpoints | Yes (`:5432`) |
| Redis | Queue / cache | Yes (`:6379`) |
| Qdrant | Vector memory (`AI_LAB_MEMORY_COLLECTION`) | Yes (`:6333`); wired into API via `QDRANT_*` in start script (IWO-053) |
| Control-plane API | FastAPI + LangGraph + Studio UI | LaunchAgent `com.ai-lab.control-plane` (`:8088`) |
| Scheduler tick | Due personal-agent schedules | LaunchAgent `com.ai-lab.scheduler-tick` (60s → `POST /v1/scheduler/tick`) |
| Agent-run worker | Background queue when enabled | In-process / env-gated (`AI_LAB_AGENT_WORKER`) |
| Backup orchestration | `scripts/backup.sh` | Scripts; first dump recorded; restore untested |
| Monitoring | Optional `observability` profile | Off |

Does **not** run large local models (route to Studio).

## Operator auth

- Bearer token in `~/.ai-lab/api.token` (fail-closed when set)
- Username/password sessions for Studio UI (PBKDF2; no token paste in chrome)
- `AI_LAB_AUTH_MODE=trusted_tailnet` still requires bearer when a token is configured (F-013)

## Memory budget (planning numbers, not measurements)

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

- Studio down: inference-dependent runs fail visibly or stay `queued`; they do not vanish.
- M1 reboot: Postgres volume is the record; LaunchAgents restart control plane + scheduler.
- Tailscale down: loopback-only services on the mini still work locally; Air/Studio cannot reach `:8088`.

## Bind address

`AI_LAB_BIND_ADDRESS` is this host's Tailscale IPv4 at deploy time (ADR 0034).
Never `0.0.0.0`. Secrets and `QDRANT_*` / `STUDIO_*` live in
`~/.ai-lab/start-control-plane.sh` (gitignored), not in LaunchAgent plists.
