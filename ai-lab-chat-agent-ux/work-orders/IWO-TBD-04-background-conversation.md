# IWO-TBD-04 — Durable background runs in conversations
**Status:** Proposed · **Depends on:** IWO-TBD-01 and worker hardening as needed

## Objective
A delegated task is owned by the mini, remains visible in its conversation, and can be retrieved after the Air/browser disconnects.

## Work
1. Reuse queued run and conversation stores; attach run cards to the originating conversation.
2. Submit once with idempotency key; show queued/running/awaiting approval/completed/failed/cancelled.
3. Poll existing run endpoints initially; reconnect and rehydrate timeline and pending approvals.
4. Verify mini worker enabled in live deployment; test Air disconnect and another-browser retrieval.
5. Investigate process restart: stale running claims, leases/locking, safe retry of side effects, and budget enforcement. Fix or explicitly gate/document limitations; do not promise recovery without proof.

## Acceptance
- Closing Air does not stop a mini-owned task while mini services remain healthy.
- Reopening conversation shows same run and result, not a duplicate.
- Restart scenario is tested and either passes documented criteria or is honestly labeled unsupported.
- No task starts a paid provider without explicit authorization.
- Tests cover duplicate submit, disconnect, cancel, failure, and awaiting approval.

## Out of scope / gates
No unattended write/PR workflow until durable recovery and exact-action approval gates pass.
