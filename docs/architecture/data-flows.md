# Data flows

**Status:** Target. Control-plane compose is not running.

```mermaid
sequenceDiagram
  actor Human
  participant Air as M3 Air
  participant API as M1 Agent API
  participant PG as PostgreSQL
  participant Redis as Redis queue
  participant Worker as Studio worker
  participant LLM as Studio Ollama
  Human->>Air: submit work order
  Air->>API: POST /work-orders
  API->>PG: insert status=created
  API->>PG: transition queued
  API->>Redis: enqueue id
  Worker->>Redis: dequeue
  Worker->>PG: running + attempt
  alt privileged tool
    Worker->>PG: awaiting_approval
    Human->>API: approve
    API->>PG: queued/running
  end
  Worker->>LLM: completion
  LLM-->>Worker: tokens
  Worker->>PG: completed + artifacts
```

## Persistence vs cache

```mermaid
flowchart LR
  WO[Work order] --> PG[(PostgreSQL)]
  WO --> Redis[(Redis queue)]
  Mem[Agent memory chunks] --> Q[(Qdrant)]
  Mem --> PG
  Redis -.->|loss is OK| PG
```

## Model bytes

Weights stay on Studio disk (`$AI_LAB_MODEL_ROOT`, default under a configurable home path). Git never sees them. The M1 stores *model ids* and routing policy only.

## Adjacent product data

Clarion/Oryntra/VolexSwarm data planes are **out of flow** unless a future work order defines a scoped MCP tool. Do not pipe production databases into Qdrant from this repo.
