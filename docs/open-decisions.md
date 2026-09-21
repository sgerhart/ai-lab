# Open decisions

Resolved items stay listed with **Resolved** and the ADR.

| ID | Decision | Status |
|----|----------|--------|
| D-001 | GitHub visibility (public vs private) | **Open** — remote is public today (F-002) |
| D-002 | GitHub identity / `github-sgerhart` origin alias | **Resolved** — ADR 0022 |
| D-003 | SPDX license vs all-rights-reserved | **Resolved** — ADR 0021 (all rights reserved) |
| D-004 | Dedicated inference host | **Resolved** — Studio (ADR 0010) |
| D-005 | Clarion VMs in-scope? | **Resolved** — adjacent only (ADR 0025) |
| D-006 | Secret store | **Resolved** (initial) — Keychain + gitignored env (ADR 0027) |
| D-007 | Initial local inference | **Resolved** — Ollama (ADR 0019) |
| D-008 | Cloud fallback | **Resolved** as *supported optional* (ADR 0016); per-job still policy |
| D-009 | Ollama bind on the Air | **Open** — live hygiene; Studio bind is Tailscale/loopback |
| D-010 | Observability stack | **Resolved** (deferred) — ADR 0026 |
| D-011 | Backup destination (not M1) | **Open** — blocks a claimed *live* restore |
| D-012 | Commit/push authorization | **Resolved** — pushed 2026-09-20 via `github-sgerhart` |
| D-013 | M1 container engine | **Resolved** — Colima (ADR 0023) |
| D-014 | LangGraph vs custom orchestrator | **Resolved** — LangGraph (ADR 0020) |
| D-015 | M3 Air unified memory attestation | **Open** — 16 GB observed, not attested |
| D-016 | Real Tailscale hostnames, tailnet name, ACL file | **Open** — placeholders only |
| D-017 | Qdrant API key on vs off for first deploy | **Resolved** — key required (ADR 0024) |
| D-018 | Thunderbolt NVMe present yet? | **Open** — paths are configurable |

Human-input leftovers before M1 deploy: D-001, D-009, D-011, D-015, D-016, D-018. See [phases/repo-complete.md](phases/repo-complete.md).
