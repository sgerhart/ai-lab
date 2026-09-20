# Roadmap

Deployment of any phase onto machines requires a separate human authorization. Repository files may exist earlier.

| Phase | Deliverable | Repo | Deployed |
|-------|-------------|------|----------|
| 0 | Foundation, ADRs, validation | Done (this revision) | n/a |
| 1 | Host bootstrap scripts, network docs, preflight | Done in Git | **No** |
| 2 | M1 compose, backup/restore, health | Done in Git | **No** |
| 3 | Studio tooling, model-serving config, ML envs | Done in Git | **No** |
| 4 | Minimum harness with durable lifecycle | LangGraph slice + FastAPI unit-tested | **No** |
| 5 | Dev / research / lab-ops agents | Deterministic plans on laptop + Studio worker | **No** |
| 6 | SLM training / eval / experiments | Layout + uv projects | **No** |
| 7 | Hardening, recovery testing, doc reconciliation | CI + runbooks | Restore **untested on live volumes** |

## Next recommended work order

[WO-006](work-orders/WO-006-phase-6-model-lab.md) — training/eval layout only until you authorize model pulls. Host apply remains [WO-001](work-orders/WO-001-phase-1-host-bootstrap.md). A commit is still D-012.
