# Troubleshooting a failed agent job

**Prerequisites:** Store access (SQLite in tests; Postgres when deployed).

**Steps:** Read `status`, `attempt_history`, `final_result`, `log_refs`. If `awaiting_approval`, it is not failed. `studio_unavailable` means the worker was unreachable (work order stays `queued`). `plan_failed` means the worker ran and the deterministic plan errored (status `failed`). Do not re-run privileged tools without approval.

**Verify:** New attempt increments `attempt_history`.

**Rollback:** `cancelled` is terminal; submit a new work order.
