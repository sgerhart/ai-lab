# ADR 0034 — Control plane may bind this host's Tailscale IPv4

- **Status:** Accepted
- **Date:** 2026-09-21
- **Related:** ADR 0012, ADR 0032

## Context

Compose and `control-plane.sh` default to `127.0.0.1`. Other tailnet nodes cannot reach loopback. ADR 0012 already said operators set `AI_LAB_BIND_ADDRESS` to the host Tailscale IPv4 at deploy time. The wrapper still refused every non-loopback address. The owner authorized Tailscale reachability from the Air.

## Decision

`scripts/control-plane.sh` may bind:

- `127.0.0.1` / `localhost` / `::1`
- the IPv4 printed by `tailscale ip -4` **on that same host**

It must refuse `0.0.0.0`, `::`, and any other address (LAN RFC1918, other nodes' Tailscale IPs).

Compose may publish the same Tailscale IPv4 **in addition to** loopback via a gitignored overlay (`infrastructure/compose.tailscale.local.yaml`). Do not commit that overlay. Do not publish `0.0.0.0`.

Tailscale membership is still not application authentication. Set `AI_LAB_API_TOKEN` when the API is reachable on the tailnet.

## Consequences

- Studio/Air can call `http://mac-mini:8088` after MagicDNS and this bind.
- ACL tags remain a console step; this ADR does not commit an ACL file.
