# Join a machine to the tailnet

**Prerequisites:** Tailscale app or CLI from Brewfile, owner credentials.

**Effects:** Node appears on the tailnet. Does not open public ports.

**Steps:** Install Tailscale. Log in. Set the machine name to match ADR 0032 (`mac-mini`, `mac-studio`, or `mac-air`). Enable MagicDNS. Copy `MagicDNSSuffix` and Tailscale IPv4 from `tailscale status --json` into `hosts/<role>/local.inventory.yaml` (gitignored). Do not assume the suffix is a GitHub org name. Apply ACL tags conceptually (`tag:ai-lab-*`) in the Tailscale admin console — do not commit the ACL.

**Verify:** `tailscale status` shows `mac-mini`, `mac-studio`, and `mac-air` when they exist. `tailscale ping mac-mini` from the Air.

**Rollback:** `tailscale logout` / disable the node in admin.
