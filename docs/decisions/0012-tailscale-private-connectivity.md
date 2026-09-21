# ADR 0012 — Tailscale for private connectivity

- **Status:** Accepted
- **Date:** 2026-09-20

## Context

Three Macs need to reach each other without publishing Postgres, Ollama, Jupyter, or agent APIs to the public Internet. A home LAN may exist (Clarion VMs on an RFC1918 /24 were observed in SSH config) but is not the AI-lab transport.

## Decision

All three lab Macs use **Tailscale** as the private network. Machine names (ADR 0032):

- `mac-mini` (inventory `m1-mini`)
- `mac-studio` (inventory `studio`)
- `mac-air` (inventory `m3-air`)

Tailnet DNS suffix remains `{{TAILNET_NAME}}` until supplied in a gitignored overlay. Do not invent IPs.

Tailscale membership is **not** application authentication. Services still need passwords/tokens and least privilege. Tailscale ACLs/grants should limit which tags can speak to Postgres, Qdrant, Redis, Ollama, and the agent API.

## Consequences

- Compose publishes to `AI_LAB_BIND_ADDRESS` (default `127.0.0.1`). Operators set that to the host Tailscale IPv4 at deploy time.
- Docker Desktop/Colima port publish to `127.0.0.1` is not reachable from other tailnet nodes.
- Reconnection: clients retry; work orders persist on the M1 (ADR 0009).

## Alternatives considered

- WireGuard DIY — more ops, no MagicDNS.
- Public HTTPS reverse proxy — rejected as default.
- Rely on home LAN only — rejects remote/dev flexibility and mixes with Clarion VMs.
