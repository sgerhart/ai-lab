# ADR 0032 — Tailscale machine names

- **Status:** Accepted (partial)
- **Date:** 2026-09-21
- **Supersedes:** the unnamed-host placeholders of ADR 0012 and open decision D-016 *for machine names only*

## Context

The owner supplied Tailscale machine names. The tailnet DNS suffix and ACL file were not supplied.

## Decision

| Inventory | Tailscale machine name |
|-----------|------------------------|
| `m1-mini` | `mac-mini` |
| `studio` | `mac-studio` |
| `m3-air` | `mac-air` |

MagicDNS FQDN remains `mac-mini.{{TAILNET_NAME}}.ts.net` until the tailnet name is recorded in a gitignored overlay. Do not invent the tailnet name, IPv4, or ACL IDs.

The MagicDNS suffix is **not** a GitHub org name. A `dentroio` guess was checked on 2026-09-21 against `tailscale status` on the Air and did not match. The observed suffix stays in `hosts/*/local.inventory.yaml` (ADR 0005).

Short names (`mac-mini`) may be used on the tailnet once MagicDNS is on.

## Consequences

- Runbooks use `mac-mini`, `mac-studio`, `mac-air`.
- IPs and the tailnet suffix stay in `hosts/*/local.inventory.yaml` (gitignored).
- Tailscale ACL tags stay conceptual until an ACL is applied in the admin console (not from this repo).
