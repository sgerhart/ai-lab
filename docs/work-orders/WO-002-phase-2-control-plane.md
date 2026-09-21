# WO-002 — Phase 2 M1 control-plane services

**Status:** Compose + backup/restore scripts in Git. **Not deployed.**  
**Phase:** 2

Acceptance (repo): pinned compose, healthchecks, mem limits, example env, backup dry-run, restore refuses overwrite.

Acceptance (deploy): compose `up` on M1, measured RAM, live restore drill after an iCloud dump has synced (ADR 0030). Throwaway restore is already tested in Git (`scripts/test-backup-restore.sh`).
