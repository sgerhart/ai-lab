# Agents

Harness identities. None of these is autonomous or production-ready. Studio chat uses the model router; a deterministic local plan still exists for scripted runs.

| Agent | Policy | Isolation | Status |
|-------|--------|-----------|--------|
| [coding-assistant](coding-assistant/README.md) | read tools; patch/commit after approval | isolated git worktree only | IWO-056 / IWO-058. Push, PR, and tests denied |
| [development](development/README.md) | bounded git | workspace allowlist | Scaffolded. Write names in policy are not the live coding path |
| [research](research/README.md) | sourced reports | HTTP allowlist | Scaffolded |
| [lab-operations](lab-operations/README.md) | **read-only** | health endpoints | Scaffolded |
| [personal](personal/README.md) | vault, files, web lookup, and research reports | `~/.ai-lab/memory`, `~/.ai-lab/files`, and `~/.ai-lab/reports` | IWO-095 reads memory. IWO-096 files finished UTC days. IWO-097 searches the web. IWO-098 reads the notes folder. IWO-099 starts it from the sidebar. IWO-100 keeps the thread. IWO-101 researches and writes a report |
| [security](security/README.md) | read inventory/preflight; lifecycle/exec after approval | isolated analysis VM only | IWO-076 policy defined. Read tools allowlisted; mutating lifecycle actions approval-gated. Live hypervisors not connected |

Catalog: [catalog.md](catalog.md)

The Studio screen for creating and running these agents is provisional. See D-019 in [docs/open-decisions.md](../docs/open-decisions.md).
