# Architecture overview

**Status:** Control plane live on `mac-mini`; Studio compute (Ollama + Jupyter)
live with several Ollama tags; Personal Agent Studio, retrieval, scheduler, and
lab MCP in use. Antares-1B UI and services live. Coding Assistant can read and,
after approval, patch an isolated worktree.  
**Updated:** 2026-09-26

A personal, three-host Apple Silicon lab with Tailscale as the private network.
Durable control-plane state lives on the M1 mini. Inference and heavy models
live on the Studio. The M3 Air is the human interface (IDE, approvals,
DefenseClaw). The security testing ground is documented in
[security-plane.md](security-plane.md) ([ADR 0040](../decisions/0040-security-plane-gateway-and-antares.md)):
that page is direction, not a running gateway.

```mermaid
flowchart TB
  subgraph human [Human plane]
    air["M3 MacBook Air\nIDE / Cursor / approvals\nDefenseClaw"]
  end
  subgraph ts [Tailscale tailnet]
    magic["MagicDNS\nmac-mini / mac-studio / mac-air"]
  end
  subgraph control [Control plane]
    mini["M1 Mac mini 16 GB\nPostgres / Qdrant / Redis\nHarness API :8088\nLaunchAgent scheduler tick"]
  end
  subgraph compute [Compute plane]
    studio["Studio M5 Max 64 GB\nOllama / Jupyter\nAntares-1B weights\n(optional workers)"]
  end
  air -->|"Studio UI / MCP stdio"| mini
  air --> magic
  magic --> mini
  magic --> studio
  mini -->|"STUDIO_OLLAMA_URL / Jupyter"| studio
  studio -->|"status / artifacts"| mini
```

## Confirmed hardware

| Inventory name | Machine | Chip | Memory | Disk | Role |
|----------------|---------|------|--------|------|------|
| `m1-mini` | Mac mini | Apple M1 | **16 GB** (confirmed) | 512 GB | Control plane |
| `studio` | Mac Studio | Apple M5 Max, 18 CPU / 40 GPU | **64 GB** (confirmed) | 1 TB | Compute plane |
| `m3-air` | MacBook Air | Apple M3 | **16 GB** (attested, ADR 0031) | 512 GB | Human plane |

## What is implemented in Git vs live

| Piece | In Git | Running on lab hosts |
|-------|--------|----------------------|
| Docs, ADRs, runbooks | Yes | n/a |
| Host Brewfiles + dry-run setup | Yes | **m1-mini `--apply` done** |
| Compose Postgres/Redis/Qdrant | Yes | **Up on mac-mini** (5432/6379/6333) |
| FastAPI control plane + LangGraph | Yes | **LaunchAgent `com.ai-lab.control-plane` :8088** |
| Personal Agent Studio (`/`, login) | Yes | **Live** (operator sessions). Sidebar item is **Agent Studio**. `/agents` and `/lab` redirect to `/` |
| Scheduler tick + LaunchAgent | Yes (IWO-030/052) | **`com.ai-lab.scheduler-tick` on mini** |
| Retrieval / Qdrant memory API | Yes (IWO-040/041/053) | **`backend=qdrant` on mini** |
| Lab as MCP server (IDE) | Yes (IWO-042/054) | **Cursor `ai-lab` on Air** |
| DefenseClaw (adjacent) | Preflight, summary API, finding glossary | **Air: Cursor + Antigravity action.** One summary stored on the mini 2026-09-25. Config edit and the API gateway are not built |
| Studio Ollama | Catalog + provider + profiles | **Default chat profile `qwen36-local` (`qwen3.6:35b-a3b`, Q4_K_M). Also `llama3.2:3b`, `qwen3.8:27b`, `qwen3-coder:30b` on `mac-studio:11434`. Listener is all interfaces (ADR 0041). Git catalog still `catalogued-not-pulled`** |
| Coding Assistant | Read tools + isolated patch/commit + short bench | **Unit-tested.** First Studio bench 2026-09-25 did not separate the models. No recorded live approved patch. Push denied |
| Studio Jupyter | Host scripts | **Up (`:8888`); token on mini** |
| Antares-1B | Runbook + `/antares` UI + jobs | **Live** UI → Studio `:8002` jobs / `:8001` completions |
| Studio SSH | Documented | **OK** — `stevengerhart@mac-studio` from Air and mini (F-015 closed) |
| Studio worker `:8090` | Scripts | **Not running** |
| Cloud LLM / deep research | Gated adapters | Off until `/secrets` authorize |

## Read next

- [control-plane.md](control-plane.md)
- [compute-plane.md](compute-plane.md)
- [agent-platform.md](agent-platform.md)
- [agent-studio.md](agent-studio.md)
- [data-flows.md](data-flows.md)
- [diagrams.md](diagrams.md)
- [security-plane.md](security-plane.md)
- [../deployment/network.md](../deployment/network.md)
- [../inventory/adjacent-systems.md](../inventory/adjacent-systems.md)
