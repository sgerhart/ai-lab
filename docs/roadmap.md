# Roadmap

Deployment onto machines requires a separate human authorization. Repository files may exist earlier.

Status columns (do not collapse them):

| Column | Meaning |
|--------|---------|
| **Code** | Implemented and tested in Git (or N/A for docs-only) |
| **Deployed** | Running on the intended lab host after authorization |
| **Live verified** | Operator exercised the live path; evidence noted |
| **Future** | Tracked as a feature (`FEAT-*`), not a phase checkbox |

## Phases 0–7 (historical build)

| Phase | Deliverable | Code | Deployed | Live verified |
|-------|-------------|------|----------|---------------|
| 0 | Foundation, ADRs, validation | Yes | n/a | n/a |
| 1 | Host bootstrap, network docs, preflight | Yes | Partial (M1 apply; Studio no) | Air↔mini Tailscale/SSH |
| 2 | M1 compose, backup/restore scripts, health | Yes | Yes (compose on mini) | Healthchecks; iCloud dump written; **restore untested** |
| 3 | Studio tooling, model-serving config | Yes | No | No |
| 4 | Minimum harness (LangGraph + FastAPI + store) | Yes | Partial (API on mini) | Submit/health from Air; Studio dispatch fails closed |
| 5 | Dev / research / lab-ops agents | Deterministic plans yes | No Studio worker | Unit/laptop tests only |
| 6 | SLM training / eval | Catalog + FakeBackend dry-run | No | No pulls |
| 7 | Hardening, recovery testing | CI + throwaway restore | Backup script used once | Live M1 restore **untested** |

Evidence notes: [phases/repo-complete.md](phases/repo-complete.md), host runbooks, [`features/index.md`](features/index.md).

Contradictory older phrases such as “API not deployed” in phase docs should be read against the **Deployed** / **Live verified** columns above and the 2026-09-21 mini bring-up—not as a claim that the Air factory or Clarion stack is part of this lab.

## Future capabilities (planned)

Owner priority order — full table in [features/index.md](features/index.md):

1. FEAT-001 Feature backlog and work-order planning — **Specified**
2. FEAT-002 Durable background execution — **Partial (live)**
3. FEAT-003 Studio worker and real model integration — **Partial (code)**
4. FEAT-004 Work-order dashboard — **Partial (live status board only)**
5. FEAT-005 Python client and IDE MCP adapter — **Not started**
6. FEAT-006 Jupyter integration — **Not started**
7. FEAT-007 Coding agent and GitHub PR workflow — **Partial (deterministic plan)**
8. FEAT-008 Research agent and retrieval memory — **Partial**
9. FEAT-009 Scheduled lab-operations agent — **Partial (on-demand only)**

## Next recommended work

1. Keep using FEAT-001 docs/issues for new ideas (no auto-execute).
2. Studio host: Tailscale `mac-studio` → `hosts/studio/setup.sh` when authorized (**FEAT-003**).
3. Do not start lab compose on the Air (ADR 0025).
