# Recovering from Studio failure

**Expected:** Control plane stays up. Jobs that need inference remain `queued` or `failed` visibly.

**Steps:** Confirm M1 compose healthy. Do not recreate Postgres. Repair or reboot Studio. When Ollama is back, queued work can be started by the orchestrator (when deployed). Re-pull models only if the disk was wiped.

**Verify:** `ollama list` on Studio; M1 work orders still present.

**Rollback:** n/a — Studio is stateless for the queue.
