# Hosts

Each host has an independently executable **[`RUNBOOK.md`](m1-mini/RUNBOOK.md)** in its directory (`m1-mini`, `studio`, `m3-air`). Clone the repo and start there.

## Operator accounts (do not conflate)

| Tailscale name | Login |
|----------------|--------|
| `mac-mini` | `sgerhart` |
| `mac-studio` | `stevengerhart` |
| `mac-air` | `stevengerhart` |

SSH examples: `sgerhart@mac-mini`, `stevengerhart@mac-studio`. See F-015 if a probe used the wrong user.

| Directory | Machine | Apply authorized? |
|-----------|---------|-------------------|
| [m1-mini/](m1-mini/README.md) | Control plane | **No** — see [m1-mini/RUNBOOK.md](m1-mini/RUNBOOK.md) |
| [studio/](studio/README.md) | Compute plane | **No** — see [studio/RUNBOOK.md](studio/RUNBOOK.md) |
| [m3-air/](m3-air/README.md) | Human plane | **No** — see [m3-air/RUNBOOK.md](m3-air/RUNBOOK.md) |
| [_template/](_template/README.md) | New host template | n/a |
| [mac-workstation/](mac-workstation/README.md) | Pointer to `m3-air` (Phase 0 name) | n/a |

Each host has `README.md`, `Brewfile`, `setup.sh`, `RUNBOOK.md`, and public-safe `inventory.yaml` (Tailscale machine name only). Scripts default to preflight/dry-run.
