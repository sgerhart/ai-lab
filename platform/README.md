# Agent platform

**Status:** LangGraph vertical slice and FastAPI control plane are **unit-tested**.  
Postgres work-order store and LangGraph checkpoints are tested against an **ephemeral local Postgres**, not the M1 compose stack. **Not deployed.**

```bash
# Laptop extras (does not deploy)
cd platform && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cd ..
PYTHONPATH=platform/src platform/.venv/bin/python -m unittest tests.test_langgraph_slice tests.test_studio_worker -v
./scripts/test-postgres-slice.sh    # throwaway postgres:16.6-alpine on 127.0.0.1:55432

# Loopback processes (optional local exercise)
./scripts/studio-worker.sh          # 127.0.0.1:8090
./scripts/control-plane.sh          # 127.0.0.1:8088; set DATABASE_URL for Postgres
```

## Responsibilities (ADR 0020)

| Concern | Implementation |
|---------|----------------|
| Work-order record | `store.py` (SQLite tests) / `postgres_store.py` (Postgres) |
| Workflow / resume | `slice_graph.py` (LangGraph) |
| HTTP control plane | `control_app.py` (FastAPI, M1) |
| Studio dispatch | `dispatch.py` |
| Studio worker | `studio_worker.py` (deterministic plans; FastAPI) |
| Agent plans | `agent_plans.py` (shared with laptop worker) |
| Permissions | `policy.py` / `approvals.py` |
| Deterministic laptop worker | `worker.py` (no LangGraph required) |

LangGraph is not the entire harness. CrewAI / AutoGen / Temporal / Celery are out of scope.
