# M1 Mac mini — control plane runbook

**Inventory name:** `m1-mini`  
**Role:** Always-on control plane (PostgreSQL, Redis, Qdrant, FastAPI + LangGraph).  
**Does not:** run large local models.

A new engineer clones `ai-lab` and follows this file only.

## Status of this runbook

| Step | Status |
|------|--------|
| Preflight script | **Implemented** (`setup.sh --preflight`). Tested on an M3 Air (chip mismatch warning is expected). **Not tested on an M1 mini.** |
| Brewfile apply | **Implemented**, default is dry-run. **Not applied** to any mini. |
| Compose file | **Implemented** (`infrastructure/compose.yaml`). `docker compose config` tested. **`up` not run.** |
| Control-plane API | **Implemented** (unit-tested with FastAPI TestClient + LangGraph MemorySaver). **Not running on an M1.** |
| Postgres store + checkpoints | **Implemented.** Tested against an ephemeral local Postgres (`scripts/test-postgres-slice.sh` / CI). **Not the M1 compose stack.** |
| Tailscale join | **Documented.** Machine name `mac-mini`. Tailnet suffix still not in Git. |
| Backup destination | **iCloud Drive** (ADR 0030). `--execute` not authorized. Live restore untested. |

Human authorization is required for `--apply`, `colima start`, `compose up`, and binding anything other than loopback.

## 1. Prerequisites

- Mac mini, Apple M1, 16 GB unified memory, 512 GB disk (confirmed).
- Admin user.
- This repository cloned.
- Homebrew **or** willingness to install it yourself (this repo will not `curl | bash`).
- Tailscale account. Do not invent the tailnet name.
- A password manager / Keychain for `POSTGRES_PASSWORD`, `REDIS_PASSWORD`, `QDRANT_API_KEY` (ADR 0027).

## 2. Preflight (safe)

```bash
cd /path/to/ai-lab
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
# Data plane
docker compose -f infrastructure/compose.yaml --env-file infrastructure/compose.local.env up -d

# Control plane (loopback). Password from compose.local.env — do not commit it.
export DATABASE_URL="postgresql://ai_lab:${POSTGRES_PASSWORD}@127.0.0.1:5432/ai_lab"
export STUDIO_WORKER_URL="http://127.0.0.1:8090"
export PYTHONPATH=/path/to/ai-lab/platform/src
./scripts/control-plane.sh
```

Do not use `compose.example.env` for a live `up`.

To let the Studio call in, set `AI_LAB_BIND_ADDRESS` to this host's Tailscale IPv4 **after** ACLs exist. The `control-plane.sh` wrapper currently **refuses** non-loopback binds; change that only with an ADR and a documented firewall exception.

## 6. Verification

```bash
docker compose -f infrastructure/compose.yaml --env-file infrastructure/compose.local.env ps
curl -sS http://127.0.0.1:8088/health
# Expect: orchestrator=langgraph, work_order_store=PostgresStore, checkpoints=postgres, deployed=false
```

Vertical slice (Studio worker must be reachable, or you will see `queued` + `studio_unavailable` — that is success for the failure path):

```bash
curl -sS -X POST http://127.0.0.1:8088/v1/work-orders \
  -H 'Content-Type: application/json' \
  -d '{"agent":"lab-operations","objective":"slice demo"}'
```

## 7. Backup / recovery

See [../../docs/runbooks/backing-up-persistent-data.md](../../docs/runbooks/backing-up-persistent-data.md).  
`./scripts/backup.sh` is dry-run unless `--execute`. Default target is iCloud Drive (ADR 0030). Restore will not overwrite live volumes automatically. **No restore has been tested against live M1 volumes.**

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
