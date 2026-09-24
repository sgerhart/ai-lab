# M1 Mac mini — control plane runbook

**Inventory name:** `m1-mini`  
**Role:** Always-on control plane (PostgreSQL, Redis, Qdrant, FastAPI + LangGraph).  
**Does not:** run large local models.

A new engineer clones `ai-lab` and follows this file only.

## Status of this runbook

| Step | Status |
|------|--------|
| Preflight script | **Tested on this M1 mini** 2026-09-21 (`./hosts/m1-mini/setup.sh --preflight`). Chip Apple M1. |
| Brewfile apply | **Applied** 2026-09-21 as `steve`. git, jq, uv, tailscale, colima, docker, docker-compose. |
| Colima | **Running** as `sgerhart` 2026-09-21 (`--cpu 2 --memory 3 --disk 40 --runtime docker --vm-type vz --network-host-addresses`). Docker context `colima`. |
| Compose file | **Running** on `mac-mini`. Healthy. Host publishes loopback + Tailscale IPv4 on **5432/6379/6333/6334**. |
| Control-plane API | **Running** as LaunchAgent `com.ai-lab.control-plane` on Tailscale **8088**. |
| Tailscale join | Mini already on tailnet as `mac-mini`. Operator SSH is `sgerhart@mac-mini`. |
| Backup destination | **iCloud Drive** (ADR 0030). First `--execute` 2026-09-21 (`20260921T194214Z`). Live restore untested. |

Human authorization is still required before cloud API enablement. Docker Desktop is uninstalled. The API is a LaunchAgent (`com.ai-lab.control-plane`).

## 1. Prerequisites

- Mac mini, Apple M1, 16 GB unified memory, 512 GB disk (confirmed).
- Admin user.
- This repository cloned at `~/workspace/github/sgerhart/ai-lab` (ADR 0035).
- Homebrew **or** willingness to install it yourself (this repo will not `curl | bash`).
- Tailscale account. Do not invent the tailnet name.
- A password manager / Keychain for `POSTGRES_PASSWORD`, `REDIS_PASSWORD`, `QDRANT_API_KEY` (ADR 0027).

## 2. Preflight (safe)

```bash
cd ~/workspace/github/sgerhart/ai-lab
./hosts/m1-mini/setup.sh --preflight
./scripts/validate-repo.sh
```

Expected: chip contains `M1`. If you run this on another Mac, you get a warning and must pass `--force` with `--apply`.

## 3. Installation (mutates the host — authorize first)

```bash
./hosts/m1-mini/setup.sh --dry-run
./hosts/m1-mini/setup.sh --apply
```

Installs: git, jq, uv, tailscale, colima, docker, docker-compose.

Engine: Colima (ADR 0023). Docker Desktop is not in the Brewfile.

```bash
colima start --cpu 2 --memory 3 --disk 40
docker version
```

## 4. Configuration

```bash
cp infrastructure/compose.example.env infrastructure/compose.local.env   # gitignored if you use *.local.env
# Set POSTGRES_PASSWORD, REDIS_PASSWORD, QDRANT_API_KEY to real values.
# Keep AI_LAB_BIND_ADDRESS=127.0.0.1 until Tailscale IPv4 is known.
# Live file on mac-mini: infrastructure/compose.local.env (gitignored, mode 600).
# Keychain copies were skipped when created over SSH.
```

Python env for the control plane:

```bash
cd platform
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Optional: `uv sync` if `uv` is on PATH.

Join Tailscale: [../../docs/runbooks/join-tailnet.md](../../docs/runbooks/join-tailnet.md). Record MagicDNS in `hosts/m1-mini/local.inventory.yaml` (gitignored).

## 5. Service startup (authorize first)

```bash
# Data plane (loopback + Tailscale overlay, never 0.0.0.0)
docker compose -f infrastructure/compose.yaml \
  -f infrastructure/compose.tailscale.local.yaml \
  --env-file infrastructure/compose.local.env up -d

# Control plane. Password from compose.local.env — do not commit it.
export DATABASE_URL="postgresql://ai_lab:${POSTGRES_PASSWORD}@127.0.0.1:5432/ai_lab"
export STUDIO_WORKER_URL="http://127.0.0.1:8090"
export STUDIO_JUPYTER_URL="http://mac-studio:8888"
export STUDIO_OLLAMA_URL="http://mac-studio:11434"
export AI_LAB_AUTH_MODE="trusted_tailnet"
export AI_LAB_BIND_ADDRESS="$(tailscale ip -4 | head -1)"
export PYTHONPATH="$HOME/workspace/github/sgerhart/ai-lab/platform/src"
./scripts/control-plane.sh
```

Do not use `compose.example.env` for a live `up`.

Live bind is this host's Tailscale IPv4 (ADR 0034), plus compose overlay for the data plane. Never `0.0.0.0`.

`STUDIO_OLLAMA_URL` must be set for `/agents` to use live Studio Ollama (IWO-019). Put the same exports in `~/.ai-lab/start-control-plane.sh` (gitignored), not in the plist.

For retrieval (FEAT-008 / IWO-053), also export `QDRANT_URL` and `QDRANT_API_KEY` in that start script (source from `infrastructure/compose.local.env` via `./scripts/wire-qdrant-env.sh --apply`; never paste keys into chat).

For Antares UI (FEAT-015 / IWO-049), export `ANTARES_JOB_URL=http://mac-studio:8002` (Studio job helper on Tailscale).

Install the LaunchAgent from the example plist (replace `OPERATOR` with this host's login). Then:

```bash
launchctl bootout "gui/$(id -u)/com.ai-lab.control-plane" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" ~/Library/LaunchAgents/com.ai-lab.control-plane.plist
launchctl enable "gui/$(id -u)/com.ai-lab.control-plane"
```

Do not put `AI_LAB_API_TOKEN` or `DATABASE_URL` in the plist; `~/.ai-lab/start-control-plane.sh` already exports them.

### Scheduler tick (IWO-052 / FEAT-009)

Minute timer for `POST /v1/scheduler/tick` (needs control plane + `~/.ai-lab/api.token`):

```bash
./scripts/install-scheduler-launchagent.sh          # dry-run
./scripts/install-scheduler-launchagent.sh --apply  # install LaunchAgent
./scripts/scheduler-tick.sh --apply                 # manual one-shot
tail -f ~/.ai-lab/scheduler-tick.log
```

`scheduler-tick.sh` prefers loopback if `/health` answers, else this host's Tailscale IPv4 (ADR 0034). Override with `AI_LAB_SCHEDULER_HOST`.

## 6. Verification

From the Air:

```bash
curl -sS http://mac-mini:8088/health
# Expect: orchestrator=langgraph, work_order_store=PostgresStore, checkpoints=postgres, deployed=true
nc -z mac-mini 5432
```

On the mini, the API does not listen on `127.0.0.1:8088` (Tailscale IPv4 only). Compose Postgres does listen on loopback `127.0.0.1:5432`.

Vertical slice (Studio worker must be reachable, or you will see `queued` + `studio_unavailable` — that is success for the failure path):

```bash
curl -sS -X POST http://mac-mini:8088/v1/work-orders \
  -H "Authorization: Bearer $(cat ~/.ai-lab/mac-mini-api.token)" \
  -H 'Content-Type: application/json' \
  -d '{"agent":"lab-operations","objective":"slice demo"}'
```

## 7. Backup / recovery

See [../../docs/runbooks/backing-up-persistent-data.md](../../docs/runbooks/backing-up-persistent-data.md).  
`./scripts/backup.sh` is dry-run unless `--execute`. Default target is iCloud Drive (ADR 0030). First dump **wrote** 2026-09-21 (`20260921T194214Z/postgres.sql`, 29712 bytes). iCloud sync to another device is **not** confirmed here. Live restore onto M1 volumes is **not** tested.

## 8. Troubleshooting

| Symptom | Check |
|---------|--------|
| Chip mismatch | You are not on the mini; do not `--apply --force` unless intentional |
| Port 5432 in use | Do not start this compose on the Air (Clarion collision) |
| `studio_unavailable` | Expected if the Studio worker is down; work order remains `queued` |
| Control plane restart | Work orders in SQLite/Postgres remain; LangGraph resume needs the same checkpointer |
| RAM pressure | Cap Colima at 3 GB; do not enable observability profile |

## 9. Rollback

```bash
docker compose -f infrastructure/compose.yaml --env-file infrastructure/compose.local.env stop
colima stop
# Do not down -v without a tested backup
```
