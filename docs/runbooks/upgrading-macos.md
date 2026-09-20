# Upgrading macOS safely

**Prerequisites:** Backups if the M1 will reboot. Pause training on the Studio.

**Effects:** Reboot, possible Docker/Colima VM breakage, possible Ollama service reset.

**Steps:** Stop compose (`stop`, not `down -v`). Stop Ollama jobs. Upgrade. After boot: Colima/Docker, compose `ps`, Ollama tags, Tailscale status.

**Verify:** Healthchecks, tailscale ping.

**Rollback:** macOS rollback is not guaranteed; this is why M1 backups matter before the upgrade.
