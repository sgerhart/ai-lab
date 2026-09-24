# Data flows

**Status:** Control plane, Studio Ollama/Jupyter, Qdrant memory, scheduler tick,
and lab MCP are **live** (2026-09-24). Studio worker `:8090` and Antares CLI
sandbox are **not** live.

## Personal agent / work order (target + live core)

```mermaid
sequenceDiagram
  actor Human
  participant Air as M3 Air
  participant API as M1 Agent API
  participant PG as PostgreSQL
  participant Q as Qdrant
  participant Tick as Scheduler LaunchAgent
  participant LLM as Studio Ollama
  Human->>Air: Studio UI / Cursor MCP
  Air->>API: chat / agent-run / memory
  API->>PG: conversations / runs / WOs
  API->>Q: memory search / upsert
  API->>LLM: completion (STUDIO_OLLAMA_URL)
  LLM-->>API: tokens
  Tick->>API: POST /v1/scheduler/tick
  API->>PG: start due agent runs
```

## Persistence vs cache

```mermaid
flowchart LR
  WO[Work order / agent run] --> PG[(PostgreSQL)]
  WO --> Redis[(Redis queue)]
  Mem[Memory chunks] --> Q[(Qdrant)]
  Mem --> PG
  Redis -.->|loss is OK| PG
```

## Model bytes

Weights stay on Studio disk (Ollama library; Antares under `~/.ai-lab/antares/`).
Git never sees them. The M1 stores *model ids* and routing policy only.

## Adjacent product data

Clarion / agentic-factory / DefenseClaw data planes are **out of flow** unless a
future work order defines a scoped bridge. Do not pipe production databases into
Qdrant from this repo. See [../inventory/adjacent-systems.md](../inventory/adjacent-systems.md).
