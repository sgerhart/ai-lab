# Open decisions

Resolved items stay listed with **Resolved** and the ADR.

| ID | Decision | Status |
|----|----------|--------|
| D-001 | GitHub visibility (public vs private) | **Resolved** — stays public (ADR 0028) |
| D-002 | GitHub identity / `github-sgerhart` origin alias | **Resolved** — ADR 0022 |
| D-003 | SPDX license vs all-rights-reserved | **Resolved** — ADR 0021 (all rights reserved) |
| D-004 | Dedicated inference host | **Resolved** — Studio (ADR 0010) |
| D-005 | Clarion VMs in-scope? | **Resolved** — adjacent only (ADR 0025) |
| D-006 | Secret store | **Resolved** (initial) — Keychain + gitignored env (ADR 0027) |
| D-007 | Initial local inference | **Resolved** — Ollama (ADR 0019) |
| D-008 | Cloud fallback | **Resolved** as *supported optional* (ADR 0016); per-job still policy |
| D-009 | Ollama bind on the Air | **Resolved** — accepted workstation risk (ADR 0029); Studio still loopback/Tailscale |
| D-010 | Observability stack | **Resolved** (deferred) — ADR 0026 |
| D-011 | Backup destination (not M1) | **Resolved** — iCloud Drive (ADR 0030). Live restore still untested |
| D-012 | Commit/push authorization | **Resolved** — pushed 2026-09-21 via `github-sgerhart` (`9756110` on `origin/main`) |
| D-013 | M1 container engine | **Resolved** — Colima (ADR 0023) |
| D-014 | LangGraph vs custom orchestrator | **Resolved** — LangGraph (ADR 0020) |
| D-015 | M3 Air unified memory attestation | **Resolved** — 16 GB (ADR 0031) |
| D-016 | Tailscale names | **Partial** — machines `mac-mini` / `mac-studio` / `mac-air` (ADR 0032). Suffix/IPv4 observed on the Air 2026-09-21 and written to gitignored overlays. **Not** `dentroio`. Studio was not on the tailnet. ACL file still unsupplied |
| D-017 | Qdrant API key on vs off for first deploy | **Resolved** — key required (ADR 0024) |
| D-018 | Thunderbolt NVMe | **Resolved** (deferred) — not in initial setup (ADR 0033) |
| D-019 | Studio agent create/run screen | **Direction accepted** — chat is the front door (IWO-059). Agent Studio is a second menu plus a canvas (ADR 0042, IWO-063). Operator has not accepted the live screen |

Still not inventable: `{{TAILNET_NAME}}`, Tailscale IPv4, ACL file contents. See [phases/repo-complete.md](phases/repo-complete.md). Current capabilities: [features/index.md](features/index.md).
