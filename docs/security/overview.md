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

## Findings (still open)

| ID | Severity | Summary | Live change? |
|----|----------|---------|--------------|
| F-001 | Critical, locally mitigated | Git was inited in the parent workspace | Relocated `.git`; not pushed |
| F-002 | High | GitHub `sgerhart/ai-lab` is public | No |
| F-003 | High | Ollama on the **Air** listens `*:11434` | No (not Studio) |
| F-004 | Medium | `~/.ollama/id_ed25519` on Air | Ignored by Git |
| F-005 | Medium | `gh` active account `dentroio` vs `sgerhart` repo | No |
| F-006 | Info | Product Docker/Postgres on the Air | Adjacent |
| F-007 | Design | Compose loopback is unreachable across tailnet | Documented; bind address at deploy |

Details of F-001–F-006: recorded 2026-09-19 on the operator workstation.

## Secret store

Still open (D-006). Until then: macOS Keychain / filled gitignored `.env` on the M1 only. Do not reuse Clarion Vault credentials in this repo.

## Data retention

Work-order rows and audit events are kept until an operator purges them. Model caches follow Studio disk policy. Logs must not be committed.

See also: [trust-boundaries.md](trust-boundaries.md), [agent-permissions.md](agent-permissions.md), [../runbooks/rotating-credentials.md](../runbooks/rotating-credentials.md).
