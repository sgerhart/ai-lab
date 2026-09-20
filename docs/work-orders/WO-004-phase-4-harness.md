# WO-004 — Phase 4 minimum agent harness

**Status:** LangGraph vertical slice + FastAPI **unit-tested**. Postgres store + checkpoints tested against ephemeral local Postgres. **Not deployed.**  
**Phase:** 4

## Acceptance (repo)

- [x] Durable work-order states
- [x] LangGraph interrupt/resume for approval
- [x] Control-plane restart resumes from the same checkpointer
- [x] Unavailable Studio leaves the work order persisted (`queued` + `studio_unavailable`)
- [x] Loopback-only server wrappers
- [x] Postgres work-order store + LangGraph checkpoints (ephemeral local Postgres; not M1)

## Acceptance (deploy)

- [ ] API running on the M1 with a Postgres checkpointer
- [ ] Studio worker running on the Studio and reachable over Tailscale
