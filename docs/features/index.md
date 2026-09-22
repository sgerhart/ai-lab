# Future capabilities index

**Updated:** 2026-09-21  
**Source:** Owner priority table (2026-09-21). GitHub issues: [#2](https://github.com/sgerhart/ai-lab/issues/2)–[#10](https://github.com/sgerhart/ai-lab/issues/10).

Lifecycle and entity definitions: [README.md](README.md). Template: [TEMPLATE.md](TEMPLATE.md).

Status legend (honest):

| Label | Meaning |
|-------|---------|
| Idea / Specified | Documented intent only |
| Partial (code) | Some modules or UI in Git |
| Partial (live) | Some host behavior verified |
| Not started | No meaningful implementation |
| Blocked | Waiting on another host or feature |

Do not treat this index as authorized implementation or deploy.

| Pri | ID | Capability | What it gives you | Target host(s) | Dependencies | Status | GitHub |
|-----|----|------------|-------------------|----------------|--------------|--------|--------|
| 1 | [FEAT-001](FEAT-001-work-order-planning-and-approval.md) | Feature backlog and work-order planning | Turn ideas into reviewed specs and bounded tasks | `mac-air` (authoring); plans land in Git | ADRs 0001, 0018, 0020 | **Specified** (this tree). No planning agent yet. | [#2](https://github.com/sgerhart/ai-lab/issues/2) |
| 2 | FEAT-002 | Durable background execution | Submit a job and close the laptop without losing it | `mac-mini` (SoT); Air submits | Control-plane API + Postgres | **Partial (live):** PostgresStore + LangGraph on `mac-mini:8088`; jobs remain `queued` when Studio is down. Full completion path needs FEAT-003. | [#3](https://github.com/sgerhart/ai-lab/issues/3) |
| 3 | FEAT-003 | Studio worker and real model integration | Replace fixed demonstration plans with useful agent work | `mac-studio` worker + models; mini dispatch | Studio on tailnet; ADR 0019/0010 | **Partial (code):** deterministic worker + Ollama client unit-tested. Studio **not** on tailnet. No model pulls. | [#4](https://github.com/sgerhart/ai-lab/issues/4) |
| 4 | FEAT-004 | Work-order dashboard | Submit, inspect, approve, retry, retrieve results | Air browser → mini API | FEAT-002 API | **Partial (live):** status board at `GET /`. No submit/approve/retry UI. | [#5](https://github.com/sgerhart/ai-lab/issues/5) |
| 5 | FEAT-005 | Python client and IDE MCP adapter | Delegate from Cursor, VS Code, or a terminal | Air client; mini API | FEAT-002; ADR on MCP servers | **Not started.** MCP allowlist deny-unlisted, **zero** servers. | [#6](https://github.com/sgerhart/ai-lab/issues/6) |
| 6 | FEAT-006 | Jupyter integration | Submit experiments from the Air; run ML on the Studio | Air client; Studio Jupyter | FEAT-003; compute-plane docs | **Not started.** Documented as Studio intent only. | [#7](https://github.com/sgerhart/ai-lab/issues/7) |
| 7 | FEAT-007 | Coding agent and GitHub PR workflow | Implement approved work orders on isolated branches | Studio/Air agents; GitHub | FEAT-001, FEAT-003; ADR 0018 | **Partial (code):** deterministic `development` plan (`repo_read`, `git_status`). No PR automation. Push/merge stay privileged. | [#8](https://github.com/sgerhart/ai-lab/issues/8) |
| 8 | FEAT-008 | Research agent and retrieval memory | Sourced research + reuse project context | Studio research; Qdrant on mini | FEAT-003; Qdrant live | **Partial (code/live):** report artifact plan tested; Qdrant container healthy on mini. No retrieval API. No LLM research loop. | [#9](https://github.com/sgerhart/ai-lab/issues/9) |
| 9 | FEAT-009 | Scheduled lab-operations agent | Approved health checks and change reports | Mini schedule or Air cron → mini API | FEAT-002; lab-ops policy | **Partial (code):** on-demand `health_read` / `compose_ps_read`. **No scheduler.** Writes still forbidden without ADR + policy. | [#10](https://github.com/sgerhart/ai-lab/issues/10) |

## Per-capability sketches

Each row above is enough for triage. Full fields (purpose, workflow, deliverables, acceptance) for priority 1 are in [FEAT-001](FEAT-001-work-order-planning-and-approval.md). Priorities 2–9 use the same shape in the tables below until individual specs are written.

### FEAT-002 — Durable background execution

| Field | Content |
|-------|---------|
| Purpose | Runtime work orders survive Air sleep and Studio outages. |
| User workflow | Air `POST /v1/work-orders` → mini Postgres → (later) Studio → approve → complete. |
| Deliverables | Already: FastAPI, PostgresStore, LangGraph checkpoints, LaunchAgent. Future: reconcile stuck `running`, clearer retry. |
| Acceptance | Laptop closed; job still in Postgres. Studio down → `queued` + visible error, not deleted. |
| Out of scope | Clarion/factory jobs; Air as always-on queue. |

### FEAT-003 — Studio worker and real model integration

| Field | Content |
|-------|---------|
| Purpose | Useful agent work on Studio models instead of fixed demo plans. |
| User workflow | Mini dispatches → Studio worker → Ollama/MLX → artifacts back to mini. |
| Deliverables | Host apply; worker service; model catalog entries; explicit `ollama pull` runbook use. |
| Acceptance | End-to-end work order reaches `awaiting_approval` or `completed` with Studio up. No silent pulls. |
| Out of scope | Air as inference plane; absorbing Clarion factory. |

### FEAT-004 — Work-order dashboard

| Field | Content |
|-------|---------|
| Purpose | Humans submit/inspect/approve/retry without raw curl. |
| User workflow | Open dashboard (Air) → act on mini API with token. |
| Deliverables | UI for list/detail/approve/retry; still Tailscale-only. |
| Acceptance | Approve a paused job from the UI; token required for mutating actions. |
| Out of scope | Public Internet dashboard. |

### FEAT-005 — Python client and IDE MCP adapter

| Field | Content |
|-------|---------|
| Purpose | Call the lab API from scripts and IDE agents under deny-by-default MCP. |
| User workflow | Install client / enable listed MCP server → submit/list/approve. |
| Deliverables | Python package; optional MCP server entry in allowlist (new ADR if needed). |
| Acceptance | Client can submit and fetch a work order against loopback or Tailscale; unlisted MCP refused. |
| Out of scope | Org-wide tokens; product factory MCP. |

### FEAT-006 — Jupyter integration

| Field | Content |
|-------|---------|
| Purpose | Author notebooks on Air; execute heavy cells on Studio. |
| User workflow | Air notebook → submit experiment work order → Studio kernel/job → results to mini/artifacts. |
| Deliverables | Documented pattern; optional gateway; Studio JupyterLab with token. |
| Acceptance | One notebook-driven job runs on Studio without Air staying awake. |
| Out of scope | Air as Jupyter *server* for the lab. |

### FEAT-007 — Coding agent and GitHub PR workflow

| Field | Content |
|-------|---------|
| Purpose | Implement **approved** implementation work orders on isolated branches; open PRs. |
| User workflow | Approved IWO → coding agent branch → tests → PR → human merge (never silent). |
| Deliverables | Agent plan + tools; PR creation behind approval; no auto-merge. |
| Acceptance | Branch + PR for a toy IWO; merge requires human. |
| Out of scope | Self-merge; writing into product repos without explicit scope. |

### FEAT-008 — Research agent and retrieval memory

| Field | Content |
|-------|---------|
| Purpose | Sourced research artifacts; retrieve relevant lab/project context from Qdrant. |
| User workflow | Research runtime WO → allowlisted fetch / local corpus → report + optional memory write. |
| Deliverables | Retrieval API; citation policy enforcement; memory write gates. |
| Acceptance | Report with sources; no fabricated citations; memory writes audited. |
| Out of scope | Unrestricted web crawl; Clarion production DB ingestion. |

### FEAT-009 — Scheduled lab-operations agent

| Field | Content |
|-------|---------|
| Purpose | Periodic approved health checks; report changes without silent remediation. |
| User workflow | Schedule (launchd/cron) → runtime WO as `lab-operations` → report artifact / notify. |
| Deliverables | Scheduler config; diff/report format; still read-only policy. |
| Acceptance | Scheduled run creates a runtime WO and a report; no write tools without new ADR. |
| Out of scope | Auto-restart hosts; auto `compose down -v`. |

## Historical phase work orders

`WO-000`–`WO-007` remain phase **implementation** records under [`../work-orders/`](../work-orders/README.md). They are not runtime Postgres jobs and are not renamed by this index.
