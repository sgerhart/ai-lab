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
| 6 | SLM training / eval / experiments | Catalog schema + FakeBackend dry-run | **No** |
| 7 | Hardening, recovery testing, doc reconciliation | CI + throwaway restore | Live restore **untested** (D-011) |

## Next recommended work order

Host apply remains [WO-001](work-orders/WO-001-phase-1-host-bootstrap.md) after you authorize it. D-011 (backup destination) still blocks a claimed live restore.
