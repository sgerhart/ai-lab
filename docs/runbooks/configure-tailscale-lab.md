# Configure Tailscale for the three-host lab

**Prerequisites:** Tailscale installed and logged in on each Mac. Operator can open the admin console.

**Effects:** MagicDNS names match ADR 0032. Compose/API may publish this host's Tailscale IPv4 (ADR 0034). Does not open the public Internet. Does not commit IPs or ACLs.

## On each Mac

```bash
# Mini
sudo tailscale set --hostname=mac-mini
# Air
sudo tailscale set --hostname=mac-air
# Studio (when joined)
sudo tailscale set --hostname=mac-studio
```

Confirm MagicDNS: `tailscale status` shows `mac-mini`, `mac-air`. `tailscale ping mac-mini`.

Copy `MagicDNSSuffix` and IPv4 into gitignored `hosts/<role>/local.inventory.yaml`.

## Publish lab ports (M1 only)

Keep loopback. Add the mini's Tailscale IPv4 via gitignored `infrastructure/compose.tailscale.local.yaml`. Never `0.0.0.0`.

`control-plane.sh` may bind that same IPv4 (ADR 0034). Set `AI_LAB_API_TOKEN` when the API is on the tailnet.

Colima must replicate host addresses (`hostAddresses: true` / `colima start --network-host-addresses`) or Docker cannot bind `100.x`.

## Admin console (human)

1. Open https://login.tailscale.com/admin/machines
2. Confirm names `mac-mini` / `mac-air` / `mac-studio`
3. Optional tags: `tag:ai-lab-control`, `tag:ai-lab-compute`, `tag:ai-lab-human`
4. ACL grants: see [../deployment/network.md](../deployment/network.md). Do not paste a tailnet id into Git.

**Verify:** From the Air: `curl -sS http://mac-mini:8088/health` and `nc -z mac-mini 5432`.

**Rollback:** `colima` / compose back to `127.0.0.1` only. `control-plane.sh` with `AI_LAB_BIND_ADDRESS=127.0.0.1`.
