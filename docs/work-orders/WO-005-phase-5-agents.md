# WO-005 — Phase 5 initial agents

**Status:** Policies plus **deterministic plans** executed by the laptop worker and the Studio HTTP worker. Tested. No LLM worker. **Not deployed.**  
**Phase:** 5

| Agent | Local plan | Honesty |
|-------|------------|---------|
| lab-operations | `health_read`, `compose_ps_read` | Reports closed ports as expected |
| research | `write_report_artifact` only | Will not fabricate citations; HTTP fetch disabled |
| development | `repo_read`, `git_status` | Bounded to `--workspace`; push is not in the plan |

Lab-ops remains read-only in `policy.json`. `git_push` is constrained out of lab-ops even if a caller asks for it. Privileged tools are not in any default plan and the plan runner refuses to execute them.

## Acceptance (repo)

- [x] Shared `agent_plans.py` for all three catalog agents
- [x] Studio worker POST `/v1/tasks` runs the plan (not an LLM)
- [x] Plan failure persists as `failed` (distinct from Studio-down re-queue)
- [x] Research plan does not invent citations
- [x] Development plan stays inside `bounded_scope`

## Acceptance (deploy)

- [ ] Studio worker process on the Studio host
- [ ] M1 dispatch over Tailscale
