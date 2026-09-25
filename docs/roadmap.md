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

Evidence: [phases/repo-complete.md](phases/repo-complete.md), [`features/index.md`](features/index.md), [`features/PLAN-mini-first.md`](features/PLAN-mini-first.md).

## Mini-first personal-agent platform (current)

Core purpose: always-on personal agents + AI experimentation. Current capability table: [features/index.md](features/index.md).

| Slice | Work | Code | Deploy | Live |
|-------|------|------|--------|------|
| Harness | IWO-002–007, 020, 031 | Done | Mini `:8088` | Chat and tool loop |
| Studio UI | FEAT-004 / FEAT-013 / IWO-059 | Chat-first shell at `/` | Mini `/` | Used. Live lab-health pass still open (D-019) |
| Models | FEAT-003 / IWO-055 | Profiles in Git; catalog not marked pulled | Studio Ollama | Three tags installed 2026-09-24 |
| Coding | FEAT-016 IWO-055/056/058 | Read + isolated patch/commit | HTML on mini | Unit only for the patch path |
| Coding eval / PR | IWO-057, FEAT-007 | Not started | — | — |
| Memory / schedule / IDE MCP | IWO-040–042, 052–054 | Done | Mini + Air | Live |
| Jupyter / Antares | FEAT-006 / FEAT-015 | Done for current UI and services | Studio | Live. Antares not set to survive reboot |
| Studio worker `:8090` | FEAT-003 optional | Scripts | No | No |

## Next

Operator is deciding the agent create/run screen (D-019). Do not treat the current form as final. Do not pull more models, enable paid APIs, or deploy hosts without a separate yes.

Still open after that decision: coding-model eval (IWO-057), pull-request delivery (FEAT-007), and the thin hardening notes on FEAT-016. Live M1 restore is still untested.
