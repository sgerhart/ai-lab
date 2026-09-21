# ADR 0030 — iCloud Drive is the initial backup destination

- **Status:** Accepted
- **Date:** 2026-09-21
- **Supersedes:** open decision D-011

## Context

Durable control-plane data lives on the M1. A backup that only sits on the same internal SSD is not a backup. The owner asked to leverage iCloud.

## Decision

Initial off-box destination is **iCloud Drive** on the operator Apple ID already used on these Macs.

- Default directory (not created by Git): `~/Library/Mobile Documents/com~apple~CloudDocs/ai-lab-backups`
- Override with `AI_LAB_BACKUP_TARGET` or `backup.sh --target` (must be under that CloudDocs tree unless `--allow-other-target`).
- Do not commit dumps. Do not write dumps into the git repository.

Honesty limits:

- iCloud Drive is **sync**, not a versioned backup appliance. Apple may evict local copies.
- A dump is off-box only after it has synced to iCloud and is visible on another device.
- `postgres.sql` can contain work-order text. Do not treat iCloud as a secrets vault.
- Throwaway restore is tested. **Restore from an iCloud dump onto live M1 volumes is not tested** and `restore.sh` still will not auto-overwrite live data.

## Consequences

- First `backup.sh --execute` (when authorized) targets iCloud Drive.
- NAS, Time Machine, or Tailscale node remain future `--allow-other-target` options, not the default.
