# ai-lab

Personal AI infrastructure and experimentation platform.

This repository is the **source of truth** for design, deployment, operation, security, recovery, and evolution of a three-host Apple Silicon lab:

| Plane | Machine | Role |
|-------|---------|------|
| Control | Mac mini (M1, 16 GB, 512 GB) | Orchestration, queues, PostgreSQL, Qdrant, Redis, monitoring, backups |
| Compute | Mac Studio (M5 Max, 64 GB, 1 TB) | Inference, MLX, training, agent workers, evaluation |
| Human | MacBook Air (M3, 16 GB, 512 GB) | IDE, Git, SSH, approvals, dashboards |

The repository name is **`ai-lab`**. Do not rename it.

**Deployment status:** M1 Postgres/Redis/Qdrant and the FastAPI control plane are **up** on `mac-mini` over Tailscale (API port **8088**). Studio is **not** started. See [docs/phases/repo-complete.md](docs/phases/repo-complete.md).

## Three areas

1. **Infrastructure** — hosts, Tailscale, compose services, backups, operations
2. **Agent platform** — harness, durable work orders, tools, MCP, approvals
3. **Model laboratory** — local inference, SLM work, datasets, evaluations

Standalone products (Clarion, Oryntra, VolexSwarm, and future apps) stay in their own repositories and connect through documented interfaces.

## Quick start (repository only)

```bash
cd /path/to/ai-lab
./scripts/preflight.sh          # repo + local tool checks; does not change hosts
./scripts/validate-repo.sh
./tests/test_structure.sh
python3 -m unittest discover -s tests -v

# Optional: exercise the harness on this machine only (SQLite, loopback).
./scripts/platform.sh --db /tmp/ai-lab-harness.sqlite submit --agent lab-operations --objective "health snapshot"
./scripts/platform.sh --db /tmp/ai-lab-harness.sqlite tick
```

Host bootstrap, compose `up`, model pulls, and service binds require an explicit human authorization. See [docs/deployment/sequence.md](docs/deployment/sequence.md).

## Repository map

| Path | Role |
|------|------|
| [`docs/`](docs/README.md) | Architecture, ADRs, operations, security, runbooks, work orders |
| [`hosts/`](hosts/README.md) | `studio`, `m1-mini`, `m3-air` Brewfiles and setup scripts |
| [`infrastructure/`](infrastructure/README.md) | Compose, Postgres, Qdrant, Redis, backup, monitoring |
| [`platform/`](platform/README.md) | Agent harness (API, orchestrator, store, router, approvals) |
| [`agents/`](agents/README.md) | Development, research, lab-operations agents |
| [`models/`](models/README.md) | Inference / MLX / training catalogs. Weights stay off Git |
| [`scripts/`](scripts/README.md) | Bootstrap, preflight, health, backup, restore |
| [`tests/`](tests/README.md) | Structure, policy, harness unit tests |
| [`.github/`](.github/workflows/repo-validation.yml) | CI that does not need the tailnet |
| [`AGENTS.md`](AGENTS.md) | Rules for coding agents |

## Working rules

1. Do not commit secrets, keys, Tailscale auth, `.env` values, weights, datasets, volumes, or backups.
2. Do not commit or push unless asked.
3. Do not deploy or mutate hosts unless asked.
4. Bind services to `127.0.0.1` by default; Tailscale IP bind is an explicit deploy-time setting.
5. Do not invent IPs, the tailnet DNS suffix, credentials, or unattested hardware. Committed Tailscale machine names are `mac-mini`, `mac-studio`, and `mac-air` (ADR 0032).
6. Record architecture changes as ADRs.

## Start here

1. [docs/architecture/overview.md](docs/architecture/overview.md)
2. [docs/phases/repo-complete.md](docs/phases/repo-complete.md)
3. [docs/decisions/0020-langgraph-orchestration.md](docs/decisions/0020-langgraph-orchestration.md)
4. Host runbooks: [m1-mini](hosts/m1-mini/RUNBOOK.md), [studio](hosts/studio/RUNBOOK.md), [m3-air](hosts/m3-air/RUNBOOK.md)
5. [docs/open-decisions.md](docs/open-decisions.md)
