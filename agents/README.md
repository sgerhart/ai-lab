# Agents

Harness identities. None of these is autonomous or production-ready. Studio chat uses the model router; a deterministic local plan still exists for scripted runs.

| Agent | Policy | Isolation | Status |
|-------|--------|-----------|--------|
| [coding-assistant](coding-assistant/README.md) | read tools; patch/commit after approval | isolated git worktree only | IWO-056 / IWO-058. Push, PR, and tests denied |
| [development](development/README.md) | bounded git | workspace allowlist | Scaffolded. Write names in policy are not the live coding path |
| [research](research/README.md) | sourced reports | HTTP allowlist | Scaffolded |
| [lab-operations](lab-operations/README.md) | **read-only** | health endpoints | Scaffolded |

The security agent in [FEAT-020](../docs/features/FEAT-020-security-compute-agent.md) is specified and not implemented. Add `agents/security/` when [IWO-076](../docs/work-orders/IWO-076-security-agent-definition-and-policy.md) is accepted and built. Until then it has no policy file and no tools.

Catalog: [catalog.md](catalog.md)

The Studio screen for creating and running these agents is provisional. See D-019 in [docs/open-decisions.md](../docs/open-decisions.md).
