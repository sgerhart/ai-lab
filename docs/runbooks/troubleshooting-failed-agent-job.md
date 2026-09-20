# Troubleshooting a failed agent job

**Prerequisites:** Store access (SQLite in tests; Postgres when deployed).

**Steps:** Read `status`, `attempt_history`, `final_result`. If `awaiting_approval`, it is not failed. If retries remain, inspect the last error. Do not re-run privileged tools without approval. Check Studio reachability if the error is transport.

**Verify:** New attempt increments `attempt_history`.

**Rollback:** `cancelled` is terminal; submit a new work order.
