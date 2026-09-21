# Checking inter-host connectivity

**Prerequisites:** All three nodes on the tailnet. IPv4 and tailnet suffix live in your gitignored overlay.

**Effects:** Read-only probes.

**Steps:** From Air: `tailscale ping mac-mini` and `mac-studio`. Then `ssh -o BatchMode=yes mac-mini hostname` after [installing-operator-ssh-keys.md](installing-operator-ssh-keys.md). Do not nmap the home LAN.

**Verify:** ping succeeds; SSH if configured.

**Rollback:** n/a
