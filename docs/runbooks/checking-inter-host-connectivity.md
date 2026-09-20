# Checking inter-host connectivity

**Prerequisites:** All three nodes on the tailnet. Placeholders replaced in your overlay.

**Effects:** Read-only probes.

**Steps:** From Air: `tailscale ping {{M1_TAILSCALE_HOSTNAME}}` and `{{STUDIO_TAILSCALE_HOSTNAME}}`. SSH only if keys already exist. Do not nmap the home LAN.

**Verify:** ping succeeds; SSH if configured.

**Rollback:** n/a
