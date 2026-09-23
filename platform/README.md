# Agent platform

**Status:** LangGraph vertical slice and FastAPI control plane are **unit-tested** and **running on `mac-mini:8088`**. Studio worker is not deployed.

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
| Conversations / agent runs | `conversation.py` + store methods |
| Personal-agent loop | `agent_loop.py` (mini; FakeBackend/scripted tests) |
| Tool runtime | `tool_runtime.py` (allowlist + approval gate) |
| Agent UI | `web/agents.html` at `/agents` |
| Workflow / resume | `slice_graph.py` (LangGraph work-order slice) |
| HTTP control plane | `control_app.py` (FastAPI, M1) |
| Studio dispatch | `dispatch.py` |
| Studio worker | `studio_worker.py` (deterministic plans; FastAPI) |
| Agent plans | `agent_plans.py` (fixture; loop is separate) |
| Model interface | `model_router.py` (billing classes; cloud disabled default) |
| Permissions | `policy.py` / `approvals.py` |
| Deterministic laptop worker | `worker.py` (no LangGraph required) |

Chat messages (`POST /v1/conversations/.../messages`) are ordinary turns. Durable
agent runs (`.../runs?execute=true`) run the mini model/tool loop. Runtime work
orders remain `POST /v1/work-orders`.
