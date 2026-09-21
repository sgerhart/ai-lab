# Lab hosts

| Name | Tailscale machine | Confirmed | Unconfirmed |
|------|-------------------|-----------|-------------|
| m1-mini | `mac-mini` | Mac mini, M1, 16 GB, 512 GB | Tailscale IPv4, LAN IP, tailnet suffix |
| studio | `mac-studio` | Mac Studio, M5 Max 18/40, 64 GB, 1 TB | Tailscale IPv4, LAN IP, first-boot ML stack |
| m3-air | `mac-air` | MacBook Air, M3, **16 GB**, 512 GB | Tailscale IPv4, LAN IP |

Do not commit serials, MACs, or Tailscale IPs. Use `hosts/<name>/local.inventory.yaml`. Public-safe names: `hosts/<name>/inventory.yaml`.
