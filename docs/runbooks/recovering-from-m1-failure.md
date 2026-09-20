# Recovering from M1 failure

**This is a lab-outage.** Queue and databases live here.

**Steps:** Restore from `AI_LAB_BACKUP_TARGET` onto replacement hardware using the restore runbook. Rejoin tailnet with the same hostname if possible. Do not promote the Studio to control plane without an ADR. Redis can start empty.

**Verify:** Postgres contains work orders; Qdrant collections exist if they were backed up.

**Rollback:** Only as good as the last **tested** backup. If D-011 is still open, you may have no backup.
