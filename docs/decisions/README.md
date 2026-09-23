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
| [0019](0019-ollama-initial-inference.md) | Ollama as initial local inference | Accepted |
| [0020](0020-langgraph-orchestration.md) | LangGraph as initial workflow orchestration | Accepted |
| [0021](0021-all-rights-reserved.md) | All-rights-reserved until SPDX | Accepted |
| [0022](0022-sgerhart-git-identity.md) | sgerhart email + `github-sgerhart` remote | Accepted |
| [0023](0023-colima-m1-engine.md) | Colima as initial M1 engine | Accepted |
| [0024](0024-qdrant-api-key-required.md) | Qdrant API key on first deploy | Accepted |
| [0025](0025-clarion-adjacent-only.md) | Clarion stays adjacent | Accepted |
| [0026](0026-observability-deferred.md) | Observability deferred | Accepted |
| [0027](0027-initial-secret-store.md) | Keychain + gitignored env | Accepted |
| [0028](0028-github-stays-public.md) | GitHub remote stays public | Accepted |
| [0029](0029-air-ollama-bind-accepted.md) | Air Ollama `*:11434` accepted | Accepted |
| [0030](0030-icloud-backup-destination.md) | iCloud Drive backup destination | Accepted |
| [0031](0031-m3-air-16gb.md) | M3 Air 16 GB attested | Accepted |
| [0032](0032-tailscale-machine-names.md) | Tailscale machine names | Accepted (partial — suffix/ACL still open) |
| [0033](0033-studio-nvme-deferred.md) | Studio NVMe deferred | Accepted |
| [0034](0034-tailscale-ipv4-bind.md) | Control plane Tailscale IPv4 bind | Accepted |
| [0035](0035-workspace-github-clone-path.md) | Operator clone path `~/workspace/github/<account>/<repo>` | Accepted |
| [0036](0036-adopt-work-order-protocol.md) | Adopt Work Order Protocol for implementation contracts | Accepted |
| [0037](0037-mini-owns-personal-agent-loop.md) | Mini owns the personal-agent loop | Accepted |
| [0038](0038-model-provider-billing-classes.md) | Model provider billing classes and subscription boundaries | Accepted |
| [0039](0039-hashicorp-vault-on-mini.md) | HashiCorp Vault on mini for lab secrets | Accepted |

Still not inventable: `{{TAILNET_NAME}}`, Tailscale IPv4, ACL file contents.
