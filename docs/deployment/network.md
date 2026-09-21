# Network and Tailscale

Machine names are committed (ADR 0032). Do not invent the tailnet suffix or IPs.

## Host naming

| Inventory | Tailscale machine name |
|-----------|------------------------|
| m1-mini | `mac-mini` |
| studio | `mac-studio` |
| m3-air | `mac-air` |

MagicDNS FQDN: `mac-mini.{{TAILNET_NAME}}.ts.net` (suffix is not in Git). Short names work on the tailnet once MagicDNS is enabled.

## Port matrix (published on `AI_LAB_BIND_ADDRESS`)

| Service | Host | Port | Public Internet |
|---------|------|------|-----------------|
| PostgreSQL | m1-mini (`mac-mini`) | 5432 | No |
| Redis | m1-mini | 6379 | No |
| Qdrant HTTP | m1-mini | 6333 | No |
| Qdrant gRPC | m1-mini | 6334 | No |
| Agent API | m1-mini | 8088 | No |
| Ollama | studio (`mac-studio`) | 11434 | No |
| JupyterLab | studio | 8888 | No (not deployed) |

## SSH

Use Tailscale SSH or SSH over MagicDNS (`mac-mini`, `mac-studio`, `mac-air`). Identity files stay on disk, never in Git.

## DNS

Prefer Tailscale MagicDNS. Do not run a lab-wide DNS server in Phase 1–2.

## Firewall

- Host firewall: deny inbound except Tailscale and established.
- Compose must not publish `0.0.0.0`.
- Home LAN access to these ports is not required and not assumed.

**Live M1 note (2026-09-21):** Docker Desktop was uninstalled. Compose and the API publish loopback plus this host's Tailscale IPv4 on the canonical ports (5432/6379/6333/6334/8088). Never `0.0.0.0`.

## Authentication

| Hop | Mechanism |
|-----|-----------|
| Node membership | Tailscale identity / tags |
| Postgres | password from env (not in Git) |
| Redis | requirepass |
| Qdrant | API key (ADR 0024) |
| Ollama | network restriction; Studio is the lab endpoint (ADR 0029) |
| Agent API | token header (planned) |

## Tailscale ACL considerations (placeholders)

Tag devices: `tag:ai-lab-control`, `tag:ai-lab-compute`, `tag:ai-lab-human`.

Grants (conceptual, not a real ACL file):

- human → control :443/8088/22
- human → compute :22
- control → compute :11434
- compute → control :5432/6379/6333/8088
- deny control postgres from the internet
- deny compute Ollama from tags other than control/human

Do not commit a Tailscale ACL with a real tailnet id.

## Failure and reconnection

Clients should retry with backoff. Work orders persist on the M1. If Tailscale is down, operators can still use loopback on the same host. The Air sleeping does not stop M1 or Studio.
