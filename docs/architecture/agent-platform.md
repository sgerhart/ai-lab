# Agent platform

**Code:** [`platform/`](../../platform/README.md)  
**Status:** LangGraph control plane **live** on `mac-mini:8088` with Personal
Agent Studio, scheduled ticks, Qdrant memory, and IDE MCP. Studio supplies
Ollama inference; Antares CLI loop not live yet.

LangGraph orchestrates **workflow steps and resume** (ADR 0020). It does not
replace PostgreSQL work-order records, tool permissions, model serving, or
Studio workers.

**Forward direction (ADR 0037 / FEAT-010):** the mini owns the **personal-agent
loop** (model → tool validate → execute/approve → observe). Studio supplies
inference and heavy workers.

**Agent Studio (ADR 0042 / FEAT-017):** chat stays the front door. The sidebar
item **Agent Studio** opens a second menu and a canvas for designing agents
that build, learn, and help run a product and a company. The live layout is
not accepted yet (D-019). See [agent-studio.md](agent-studio.md).

## Separation

```text
Human / UI (M3 Air) + Cursor MCP + DefenseClaw (adjacent)
    |
FastAPI control plane (M1) + LangGraph agent loop
    |
    +-- Conversations / agent runs     PostgreSQL
    +-- Work-order intake              FastAPI
    +-- Durable task state             PostgreSQL
    +-- Workflow + checkpoints         LangGraph (Postgres saver)
    +-- Model router                   Studio Ollama (+ gated cloud)
    +-- Scheduler tick                 LaunchAgent → POST /v1/scheduler/tick
    +-- Retrieval / memory             Qdrant (+ hash embeds); gated memory_write
    +-- Lab MCP server (stdio)         IDE tools → HTTP API (FEAT-005)
    +-- Agent MCP client               deny-unlisted allowlist (FEAT-013)
    +-- Tool permissions               policy.json + approvals
    +-- Human approvals                graph interrupt + UI/API
    |
Studio (M5 Max)
    |
Ollama / Jupyter / Antares weights / optional workers
```

Do not add CrewAI, AutoGen, Temporal, or Celery without a new ADR.

## MCP: two directions

1. **Lab as MCP server** (FEAT-005) — `scripts/lab-mcp-server.sh` for Cursor/IDEs
   (`lab_health`, `lab_memory_*`, `lab_scheduler_status`). Wired on Air (IWO-054).
2. **Agents as MCP clients** (FEAT-013) — deny-unlisted; not the same allowlist.

## Vertical slice (tested)

Submit work order → persist → LangGraph → (optional Studio worker) → approval →
complete. Studio unavailable leaves work orders `queued` with
`studio_unavailable`.

Also live: Studio chat at `/` via Studio Ollama (picker lists installed tags; `/agents` redirects);
schedule tick API + host timer; memory upsert/search against Qdrant; Cursor
`lab_health` over Tailscale; `/antares` vuln-localize UI (Studio jobs `:8002`,
human review only). Coding Assistant reads a workspace and can patch a separate
worktree after approval. Capability table: [../features/index.md](../features/index.md).
