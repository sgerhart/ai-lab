# Architecture decision records

ADRs are numbered and dated. To change a decision, add a new ADR that supersedes the old one. Do not rewrite history.

## Foundation (Phase 0 original)

| ID | Title | Status |
|----|-------|--------|
| [0001](0001-repository-as-source-of-truth.md) | This repository is the lab source of truth | Accepted |
| [0002](0002-git-root-is-ai-lab.md) | Git root is `ai-lab` | Accepted |
| [0003](0003-secrets-and-artifacts-stay-out-of-git.md) | Secrets, weights, and datasets stay out of Git | Accepted |
| [0004](0004-directory-layout.md) | Original root layout | Superseded by 0008 |
| [0005](0005-public-repository-inventory-boundary.md) | Alias-only inventory while remote is public | Accepted |
| [0006](0006-phase-gated-delivery.md) | Phase-gated *deployment* | Accepted (clarified by 0008) |
| [0007](0007-lab-is-not-a-product-monorepo.md) | Product repos remain separate | Accepted |

## Three-host platform

| ID | Title | Status |
|----|-------|--------|
| [0008](0008-keep-ai-lab-name-and-expanded-layout.md) | Keep name `ai-lab`; expand layout | Accepted |
| [0009](0009-m1-mini-control-plane.md) | M1 mini is the control plane | Accepted |
| [0010](0010-studio-compute-plane.md) | Studio is the compute plane | Accepted |
| [0011](0011-m3-air-human-plane.md) | M3 Air is the human/development plane | Accepted |
| [0012](0012-tailscale-private-connectivity.md) | Tailscale for private host connectivity | Accepted |
| [0013](0013-docker-compose-control-plane.md) | Docker Compose for initial control-plane services | Accepted |
| [0014](0014-postgres-qdrant-redis.md) | PostgreSQL, Qdrant, and Redis responsibilities | Accepted |
| [0015](0015-uv-for-new-python-pyenv-compat.md) | `uv` for new projects; keep `pyenv` compatibility | Accepted |
| [0016](0016-local-and-cloud-models.md) | Provider-neutral local and cloud models | Accepted |
| [0017](0017-agent-execution-isolation.md) | Agent execution isolation levels | Accepted |
| [0018](0018-human-approval-privileged-actions.md) | Human approval for privileged actions | Accepted |
| [0020](0020-langgraph-orchestration.md) | LangGraph as initial workflow orchestration | Accepted |

Not yet ADRs (still open): secret store, backup destination, Docker engine on M1 (Colima vs Desktop), M3 RAM attestation, GitHub visibility.
