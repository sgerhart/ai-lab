# ai-lab

Personal AI infrastructure and experimentation platform.

This repository is the **source of truth** for design, deployment, operation, security, recovery, and evolution of a three-host Apple Silicon lab:

| Plane | Machine | Role |
|-------|---------|------|
| Control | Mac mini (M1, 16 GB, 512 GB) | Orchestration, queues, PostgreSQL, Qdrant, Redis, monitoring, backups |
| Compute | Mac Studio (M5 Max, 64 GB, 1 TB) | Inference, MLX, training, agent workers, evaluation |
| Human | MacBook Air (M3, 16 GB, 512 GB) | IDE, Git, SSH, approvals, dashboards |

The repository name is **`ai-lab`**. Do not rename it.

**Deployment status:** M1 Postgres/Redis/Qdrant and the FastAPI control plane are **up** on `mac-mini` over Tailscale (API port **8088**). Studio Jupyter + Ollama are **up** on `mac-studio`. Lab site `/lab` live. `/agents` chat and tool loop use Studio `llama3.2:3b` (IWO-019/020). OpenAI/Anthropic adapters are gated behind `/secrets` authorize + keys (IWO-021; no live $ until you enable). See [docs/phases/repo-complete.md](docs/phases/repo-complete.md).

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
| [`docs/`](docs/README.md) | Architecture, ADRs, operations, security, runbooks, work orders, **features** |
| [`docs/features/`](docs/features/README.md) | Future capabilities (`FEAT-*`); not runtime jobs |
| [`docs/work-order-protocol/`](docs/work-order-protocol/README.md) | Protocol adoption; IWO vs runtime lifecycle |
| [`AGENT_PROCESS.md`](AGENT_PROCESS.md) | Agent front door for Implementation Work Orders |
| [`templates/WO-template.md`](templates/WO-template.md) | Canonical IWO template |
| [`hosts/`](hosts/README.md) | `studio`, `m1-mini`, `m3-air` Brewfiles and setup scripts |
| [`infrastructure/`](infrastructure/README.md) | Compose, Postgres, Qdrant, Redis, backup, monitoring |
| [`platform/`](platform/README.md) | Agent harness (API, orchestrator, store, router, approvals) |
| [`agents/`](agents/README.md) | Development, research, lab-operations agents |
| [`models/`](models/README.md) | Inference / MLX / training catalogs. Weights stay off Git |
| [`scripts/`](scripts/README.md) | Bootstrap, preflight, health, backup, restore |
| [`tests/`](tests/README.md) | Structure, policy, harness unit tests |
| [`.github/`](.github/workflows/repo-validation.yml) | CI that does not need the tailnet |
| [`AGENTS.md`](AGENTS.md) | Rules for coding agents (identity, secrets, deploy auth) |

## Working rules

1. Do not commit secrets, keys, Tailscale auth, `.env` values, weights, datasets, volumes, or backups.
2. Do not commit or push unless asked.
3. Do not deploy or mutate hosts unless asked.
4. Bind services to `127.0.0.1` by default; Tailscale IP bind is an explicit deploy-time setting.
5. Do not invent IPs, the tailnet DNS suffix, credentials, or unattested hardware. Committed Tailscale machine names are `mac-mini`, `mac-studio`, and `mac-air` (ADR 0032).
6. Record architecture changes as ADRs.

## Start here

1. [docs/architecture/overview.md](docs/architecture/overview.md)
2. [AGENT_PROCESS.md](AGENT_PROCESS.md) — Implementation Work Orders
3. [docs/phases/repo-complete.md](docs/phases/repo-complete.md)
4. [docs/features/index.md](docs/features/index.md) — future capabilities backlog
5. [docs/decisions/0020-langgraph-orchestration.md](docs/decisions/0020-langgraph-orchestration.md)
6. Host runbooks: [m1-mini](hosts/m1-mini/RUNBOOK.md), [studio](hosts/studio/RUNBOOK.md), [m3-air](hosts/m3-air/RUNBOOK.md)
7. [docs/open-decisions.md](docs/open-decisions.md)
