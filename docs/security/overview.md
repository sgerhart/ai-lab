# Security overview

**Status:** Policy and findings. Controls in Git. Host hardening **not applied**.

## Requirements

- Least privilege and separate agent identities
- Control plane vs compute plane (ADRs 0009–0010)
- Human approval for privileged tools (ADR 0018)
- Secrets never in Git (ADR 0003)
- Tool allowlists per work order
- Scoped credentials (no org-wide GitHub tokens in agent env)
- Audit trails on work orders
- Container isolation is tier 2, not malware-grade (ADR 0017)
- VM isolation is future, not implemented
- Network: Tailscale + loopback default; no public dashboards
- Tailscale ≠ application authentication
- Credential rotation and recovery runbooks
- Untrusted repos/prompts: no silent host privileges
- **No malware-analysis environment in this project**

## Bootstrap rules

No bootstrap script may weaken SSH, disable security controls, change firewall policy, or enable public access. `setup.sh` without `--apply` makes no changes.

## Bind policy

| Default in Git | Deploy-time exception |
|----------------|----------------------|
| `AI_LAB_BIND_ADDRESS=127.0.0.1` | Set to Tailscale IPv4 of that host |
| Never `0.0.0.0` in committed compose | Not allowed without a new ADR |

Do not expose PostgreSQL, Redis, Qdrant, Jupyter, model APIs, agent admin, or monitoring to the public Internet.

## Findings

| ID | Severity | Summary | Live change? |
|----|----------|---------|--------------|
| F-001 | Critical, locally mitigated | Git was inited in the parent workspace | Relocated `.git` into `ai-lab`. Pushed to `sgerhart/ai-lab` via `github-sgerhart`. |
| F-002 | High | GitHub `sgerhart/ai-lab` is public | **Accepted** (ADR 0028) |
| F-003 | High | Ollama on the **Air** listens `*:11434` | **Accepted** workstation risk (ADR 0029); not Studio |
| F-004 | Medium | `~/.ollama/id_ed25519` on Air | Ignored by Git |
| F-005 | Medium | `gh` active account `dentroio` vs `sgerhart` repo | No |
| F-006 | Info | Product Docker/Postgres on the Air | Adjacent |
| F-007 | Design | Compose loopback is unreachable across tailnet | Documented; bind address at deploy |
| F-012 | Medium | Mini control-plane start script exposed in operator chat | **Rotate** API token + DB password; [findings/F-012](findings/F-012-control-plane-start-script-exposure.md) |

Details of F-001–F-006: recorded 2026-09-19 on the operator workstation. F-012: 2026-09-23.

## Secret store

Initial: Keychain + gitignored env (ADR 0027). Shared lab / foundation API keys:
HashiCorp Vault on the mini (ADR 0039) — scaffold only until deploy authorized.
Values are not in Git.

## Data retention

Work-order rows and audit events are kept until an operator purges them. Model caches follow Studio disk policy. Logs must not be committed.

See also: [trust-boundaries.md](trust-boundaries.md), [agent-permissions.md](agent-permissions.md), [../runbooks/rotating-credentials.md](../runbooks/rotating-credentials.md).
