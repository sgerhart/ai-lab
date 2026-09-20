# Open decisions

Resolved items stay listed with **Resolved** and the ADR.

| ID | Decision | Status |
|----|----------|--------|
| D-001 | GitHub visibility (public vs private) | **Open** |
| D-002 | GitHub identity / `github-sgerhart` origin alias | **Open** |
| D-003 | SPDX license vs all-rights-reserved | **Open** — `LICENSE` is all-rights-reserved until an ADR |
| D-004 | Dedicated inference host | **Resolved** — Studio (ADR 0010) |
| D-005 | Clarion VMs in-scope? | **Open** — default adjacent-only |
| D-006 | Secret store | **Open** |
| D-007 | Initial local inference | **Resolved** — Ollama (ADR 0019) |
| D-008 | Cloud fallback | **Resolved** as *supported optional* (ADR 0016); per-job still policy |
| D-009 | Ollama bind on the Air | **Open** as workstation hygiene; Studio bind is Tailscale/loopback (ADR 0012/0019) |
| D-010 | Observability stack | **Open** — profile off |
| D-011 | Backup destination (not M1) | **Open** — blocks a claimed restore |
| D-012 | Commit/push authorization | **Resolved for this tree** — pushed 2026-09-20 to `sgerhart/ai-lab` via `github-sgerhart`. Repo is **public** (F-002). |
| D-013 | M1 container engine: Colima vs Docker Desktop | **Open** — Colima preferred |
| D-014 | LangGraph vs custom orchestrator | **Resolved** — LangGraph (ADR 0020) |
| D-015 | M3 Air unified memory attestation | **Open** — 16 GB observed, not attested |
| D-016 | Real Tailscale hostnames, tailnet name, ACL file | **Open** — placeholders only |
| D-017 | Qdrant API key on vs off for first deploy | **Open** — prefer on |
| D-018 | Thunderbolt NVMe present yet? | **Open** — paths are configurable |

When you decide, add an ADR and mark the row resolved.
