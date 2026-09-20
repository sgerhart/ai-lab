# Join a machine to the tailnet

**Prerequisites:** Tailscale app or CLI from Brewfile, owner credentials. Real tailnet name is **not** in Git.

**Effects:** Node appears on the tailnet. Does not open public ports.

**Steps:** Install Tailscale. Log in. Enable MagicDNS. Record hostname in `hosts/<role>/local.inventory.yaml` (gitignored). Apply ACL tags conceptually (`tag:ai-lab-*`) in the Tailscale admin console — do not commit the ACL.

**Verify:** `tailscale status` shows the other two lab nodes when they exist.

**Rollback:** `tailscale logout` / disable the node in admin.
