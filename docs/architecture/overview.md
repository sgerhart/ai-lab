# Architecture overview

**Status:** Data plane and FastAPI control plane live on the M1 mini (Tailscale, canonical ports). Studio **not** deployed. Docker Desktop uninstalled.  
**Updated:** 2026-09-21

A personal, three-host Apple Silicon lab with Tailscale as the private network. Durable control-plane state lives on the M1 mini. Inference and training live on the Studio. The M3 Air is the human interface.

```mermaid
flowchart TB
  subgraph human [Human plane]
    air["M3 MacBook Air\nIDE / Git / approvals"]
  end
  subgraph ts [Tailscale tailnet]
    magic["MagicDNS\nmac-mini / mac-studio / mac-air\n+ {{TAILNET_NAME}}.ts.net"]
  end
  subgraph control [Control plane]
    mini["M1 Mac mini 16 GB\nPostgres / Qdrant / Redis\nHarness API / scheduler"]
  end
  subgraph compute [Compute plane]
    studio["Studio M5 Max 64 GB\nOllama / MLX / workers\nJupyterLab"]
  end
  air --> magic
  magic --> mini
  magic --> studio
  mini -->|"work items / model route"| studio
  studio -->|"status / artifacts"| mini
```

## Confirmed hardware

| Inventory name | Machine | Chip | Memory | Disk | Role |
|----------------|---------|------|--------|------|------|
| `m1-mini` | Mac mini | Apple M1 | **16 GB** (confirmed) | 512 GB | Control plane |
| `studio` | Mac Studio | Apple M5 Max, 18 CPU / 40 GPU | **64 GB** (confirmed) | 1 TB | Compute plane |
| `m3-air` | MacBook Air | Apple M3 | **16 GB** (attested, ADR 0031) | 512 GB | Human plane |

Observed on the workspace host (2026-09-19) and attested by the owner (2026-09-21, ADR 0031): 16 GB unified memory.

## What is implemented in Git vs live

| Piece | In Git | Running on lab hosts |
|-------|--------|----------------------|
| Docs, ADRs, runbooks | Yes | n/a |
| Host Brewfiles + dry-run setup | Yes | **m1-mini `--apply` done** |
| Compose Postgres/Redis/Qdrant | Yes | **Up on mac-mini** (5432/6379/6333, loopback + Tailscale IPv4) |
| Agent harness + three catalog plans | Yes (deterministic; not LLM) | **API on mac-mini:8088** |
| Models | `catalog.json` (empty of pulls) + FakeBackend dry-run | None pulled from this repo |
| MCP allowlist | Yes (empty / deny-unlisted) | No servers |
| Ollama HTTP client | Loopback only; pull refused | Not pointed at Studio |
| Tailscale | Documented (`mac-mini` / `mac-studio` / `mac-air`; suffix not in Git) | Air + mini on tailnet; Studio not seen |

## Read next

- [control-plane.md](control-plane.md)
- [compute-plane.md](compute-plane.md)
- [agent-platform.md](agent-platform.md)
- [data-flows.md](data-flows.md)
- [diagrams.md](diagrams.md)
- [../deployment/network.md](../deployment/network.md)
