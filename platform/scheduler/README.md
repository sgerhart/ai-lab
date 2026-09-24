Runtime: in-process `Orchestrator.tick` / `hydrate_queue` plus the LangGraph control-plane graph.

Personal agent schedules (FEAT-009 / IWO-030): authenticated
`POST /v1/scheduler/tick` evaluates `schedule_cron` on agent definitions.
Use `scripts/scheduler-tick.sh` (dry-run by default; `--apply` to POST).

A dedicated Celery/Temporal daemon is **not** used (ADR 0020). Installing a
host LaunchAgent/crontab remains a separate deploy authorization.
