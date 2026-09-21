Runtime: in-process `Orchestrator.tick` / `hydrate_queue` plus the LangGraph control-plane graph.

A dedicated scheduler daemon is **not** required for the first M1 deploy. Do not add Celery/Temporal (ADR 0020).
