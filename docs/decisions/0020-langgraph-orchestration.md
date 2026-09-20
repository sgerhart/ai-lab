# ADR 0020 — LangGraph as initial workflow orchestration

- **Status:** Accepted
- **Date:** 2026-09-20
- **Supersedes:** open decision D-014

## Context

The harness already has a durable work-order record, a state machine, approvals, and a deterministic local worker. It still needs a resumable workflow engine so a control-plane restart or a human approval pause does not lose in-flight work.

Candidates that were **not** selected: CrewAI, AutoGen, Temporal, Celery. They are not to be added unless a later ADR shows LangGraph plus the dispatch design cannot meet a specific requirement.

## Decision

Use **LangGraph (Python)** as the initial agent *workflow* orchestrator.

A small **FastAPI** process on the **M1 mini** is the control-plane HTTP surface. It owns:

| Responsibility | Owner | LangGraph? |
|----------------|-------|------------|
| Work-order record (authoritative) | PostgreSQL via the harness store | No |
| Workflow steps and resume | LangGraph | Yes |
| Workflow checkpoints | PostgreSQL (`langgraph-checkpoint-postgres`) | Yes |
| Scheduling / hydrate after restart | Control-plane process | Uses checkpoints |
| Job dispatch to Studio | Explicit HTTP worker client | Called from a graph node |
| Model serving | Ollama on Studio (ADR 0019) | No |
| Tool permissions | `policy.json` + `approvals.py` (ADR 0018) | Enforced in nodes |
| Human approvals | Graph `interrupt` + FastAPI resume | Trigger only |

LangGraph does **not** replace the harness, the work-order schema, Postgres as source of truth, or the Studio worker.

Compute-intensive and isolated execution runs on the **Studio** worker process. The M1 graph node calls that worker over Tailscale (loopback in local tests).

Do not add CrewAI, AutoGen, Temporal, or Celery without a new ADR.

## Consequences

- Control plane depends on `langgraph`, `fastapi`, `httpx`, `psycopg`.
- Tests use an in-memory LangGraph checkpointer unless `DATABASE_URL` is set. CI and `scripts/test-postgres-slice.sh` run against ephemeral Postgres. The M1 compose stack is not used for those tests.
- Vertical slice: submit → persist → graph → Studio worker → approval interrupt → resume → complete.
- Studio down: the work order remains persisted with a visible `studio_unavailable` error and status `queued` or `failed` per policy — it must not vanish.
- Existing stdlib CLI/worker remains for laptop exercises without LangGraph installed; the FastAPI slice is the path toward M1 deploy.

## Alternatives considered

- Keep only the custom orchestrator — rejected; no checkpoint/resume story.
- Temporal / Celery — extra ops on a 16 GB M1; not justified for one workflow.
- CrewAI / AutoGen — overlapping agent runtimes; would blur permissions and approvals.
