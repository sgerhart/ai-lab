# WO-002 — Phase 2 M1 control-plane services

**Status:** Compose **up** on M1 2026-09-21 (Tailscale + loopback, canonical ports). FastAPI **up** on port 8088 via LaunchAgent. First iCloud `pg_dump` written; live restore drill **not** done.  
**Phase:** 2

Acceptance (repo): pinned compose, healthchecks, mem limits, example env, backup dry-run, restore refuses overwrite.

Acceptance (deploy): compose `up` on M1 **done** (loopback). Measured Colima RAM budget still the 3 GiB VM. Live restore drill after an iCloud dump has synced (ADR 0030) is **not** done. Throwaway restore is already tested in Git (`scripts/test-backup-restore.sh`).
