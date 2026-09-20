# Compute plane (Mac Studio)

**Host directory:** [`hosts/studio/`](../../hosts/studio/README.md)  
**Status:** Designed and encoded. **Not deployed.**  
**Chip compatibility:** M5 Max was not exercised in this workspace.

## Runs here

- Ollama (initial HTTP inference)
- MLX / MLX-LM (native Apple Silicon experiments)
- PyTorch / Hugging Face via a uv project
- JupyterLab (loopback or Tailscale bind at deploy time)
- Agent workers that execute approved tools
- Evaluation jobs

Does **not** own PostgreSQL data, the work-order queue, or backup source-of-truth.

## Memory

64 GB unified is shared with macOS, GPU, apps, and any containers. Serving configs must set explicit context and parallel limits. Do not autoload several 30B+ models.

## Storage

Initial weights and datasets: internal 1 TB SSD, paths in `models/` catalogs. Keep `AI_LAB_MODEL_ROOT` configurable for a future Thunderbolt NVMe.

Never download weights in `setup.sh`.

## Workers vs control plane

```text
M1 orchestrator --Tailscale--> Studio worker
Studio worker --HTTP--> local Ollama (localhost)
Studio worker --HTTP--> M1 API (status, artifacts)
```

If Ollama is bound only to Studio loopback, workers on the Studio can use it. The M1 router should call Studio Ollama via Tailscale, which requires a Tailscale-scoped listen on the Studio — deploy-time, not bootstrap default.

## Jupyter

JupyterLab is a compute-plane tool. Token required. Do not expose it to the public Internet. Do not make the Air a required Jupyter *server*.
