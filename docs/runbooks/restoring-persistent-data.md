# Restoring persistent data

**Prerequisites:** A dump that has already been restored successfully onto a throwaway Postgres. Human at the keyboard.

**Effects:** Would replace live data. `scripts/restore.sh` **refuses to auto-apply** even with `--confirm-restore YES-RESTORE-LIVE`.

**Steps:**
1. Restore dump into a disposable container; run queries.
2. Stop writers (`compose stop` platform, when it exists).
3. Follow a manual volume replace documented at restore time — not a one-liner in Git.

**Verify:** Work-order counts match the dump.

**Rollback:** Keep the previous volume copy. If you skipped that, you are in disaster territory (M1 failure runbook).
