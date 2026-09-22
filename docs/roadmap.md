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

## Mini-first personal-agent platform (forward)

Core purpose: always-on personal agents + AI experimentation—not an autonomous coding factory.

| Slice | Work | Code | Deploy | Live |
|-------|------|------|--------|------|
| Planning | Protocol + FEAT-010/011 + IWOs | Docs | n/a | n/a |
| Mini 1 | IWO-002 + IWO-003 (contract + auth UI, FakeBackend) | Planned | Needs auth to roll to mini | — |
| Mini 2 | IWO-004 + IWO-005 (router + model/tool loop) | Planned | Cloud $ needs auth | — |
| Mini 3 | IWO-006 + IWO-007 (recovery + action approvals) | Planned | — | — |
| Studio Jupyter | FEAT-006 / IWO-011…015 | Planned | Host auth | — |
| Studio inference | FEAT-003 + Ollama provider | Partial code | Host auth | — |
| Later | FEAT-005/008/009; optional FEAT-007 | — | — | — |

## Feature list

Full table: [features/index.md](features/index.md).

## Next recommended work

1. Merge planning PR; then implement **IWO-002** (conversation/agent-run contract).
2. Do **not** deploy hosts, pull models, or enable paid APIs without separate auth.
3. Parallel when authorized: Studio Tailscale + Jupyter (FEAT-006).
