# Checking inter-host connectivity

**Prerequisites:** All three nodes on the tailnet. IPv4 and tailnet suffix live in your gitignored overlay.

**Effects:** Read-only probes.

**Steps:** From Air: `tailscale ping mac-mini` and `mac-studio`. SSH only if keys already exist. Do not nmap the home LAN.

**Verify:** ping succeeds; SSH if configured.

**Rollback:** n/a
