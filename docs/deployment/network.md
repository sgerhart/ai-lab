# Network and Tailscale

Placeholders only. Do not invent real names.

## Host naming convention

| Inventory | Suggested Tailscale hostname (placeholder) |
|-----------|--------------------------------------------|
| m1-mini | `{{M1_TAILSCALE_HOSTNAME}}` |
| studio | `{{STUDIO_TAILSCALE_HOSTNAME}}` |
| m3-air | `{{M3_TAILSCALE_HOSTNAME}}` |

MagicDNS form: `{{HOST}}.{{TAILNET_NAME}}.ts.net` (exact suffix depends on tailnet; do not guess).

## Port matrix (published on `AI_LAB_BIND_ADDRESS`)

| Service | Host | Port | Public Internet |
|---------|------|------|-----------------|
| PostgreSQL | m1-mini | 5432 | No |
| Redis | m1-mini | 6379 | No |
| Qdrant HTTP | m1-mini | 6333 | No |
| Qdrant gRPC | m1-mini | 6334 | No |
| Agent API | m1-mini | 8088 | No (not deployed) |
| Ollama | studio | 11434 | No |
| JupyterLab | studio | 8888 | No (not deployed) |

## SSH

Use Tailscale SSH or SSH over MagicDNS. Identity files stay on disk, never in Git. Host aliases belong in a gitignored overlay, not in committed `~/.ssh/config` snippets with real names.

## DNS

Prefer Tailscale MagicDNS. Do not run a lab-wide DNS server in Phase 1–2.

## Firewall

- Host firewall: deny inbound except Tailscale and established.
- Compose must not publish `0.0.0.0`.
- Home LAN access to these ports is not required and not assumed.

## Authentication

| Hop | Mechanism |
|-----|-----------|
| Node membership | Tailscale identity / tags |
| Postgres | password from env (not in Git) |
| Redis | requirepass |
| Qdrant | API key env (optional until deploy; prefer on) |
| Ollama | network restriction + later reverse-proxy auth if exposed beyond Studio workers |
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
