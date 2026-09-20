# ADR 0012 — Tailscale for private connectivity

- **Status:** Accepted
- **Date:** 2026-09-20

## Context

Three Macs need to reach each other without publishing Postgres, Ollama, Jupyter, or agent APIs to the public Internet. A home LAN may exist (Clarion VMs on an RFC1918 /24 were observed in SSH config) but is not the AI-lab transport.

## Decision

All three lab Macs use **Tailscale** as the private network. Service URLs use MagicDNS placeholders until real names are supplied:

- `{{M1_TAILSCALE_HOSTNAME}}`
- `{{STUDIO_TAILSCALE_HOSTNAME}}`
- `{{M3_TAILSCALE_HOSTNAME}}`
- `{{TAILNET_NAME}}`

Do not invent tailnet names or IPs. Compose publishes to `AI_LAB_BIND_ADDRESS` (default `127.0.0.1`). Operators set that to the host Tailscale IPv4 at deploy time.

Tailscale membership is **not** application authentication. Services still need passwords/tokens and least privilege. Tailscale ACLs/grants should limit which tags can speak to Postgres, Qdrant, Redis, Ollama, and the agent API.

## Consequences

- Docker Desktop/Colima port publish to `127.0.0.1` is not reachable from other tailnet nodes. Deploy docs must set the bind address or use Tailscale serve — an operational step, not a default in Git.
- Reconnection: clients retry; work orders persist on the M1 (ADR 0009).

## Alternatives considered

- WireGuard DIY — more ops, no MagicDNS.
- Public HTTPS reverse proxy — rejected as default.
- Rely on home LAN only — rejects remote/dev flexibility and mixes with Clarion VMs.
