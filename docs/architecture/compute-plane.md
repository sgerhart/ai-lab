# Compute plane (Mac Studio)

**Host directory:** [`hosts/studio/`](../../hosts/studio/README.md)  
**Status:** Ollama + JupyterLab **live** on `mac-studio` (Tailscale). Studio
worker API (`:8090`) **not** running. SSH as `stevengerhart@mac-studio` works
from Air and mini ([F-015](../security/findings/F-015-studio-ssh-auth-failure.md) closed).

**Chip:** M5 Max (attested).

## Runs here

| Component | Live |
|-----------|------|
| Ollama | Yes — `qwen3.6:35b-a3b` (Q4_K_M, chat default `qwen36-local`), `qwen3.8:27b`, `qwen3-coder:30b`, `llama3.2:3b` on `:11434` (all interfaces, ADR 0041). Install is not the same as loaded. Intended cap is one resident tag; the live agent does not set that cap yet. Operator role assignments are a mini file, not this host |
| JupyterLab | Yes — `:8888` (token on mini `~/.ai-lab/studio-jupyter.token`) |
| MLX / transformers (Jupyter venv) | Present; used for Antares load smoke |
| Antares-1B + completions + jobs | Weights; loopback `:8001`; Tailscale jobs `:8002`; mini `/antares` |
| Studio worker (`scripts/studio-worker.sh`) | Not running |
| Evaluation / heavy training jobs | As authorized |

Does **not** own PostgreSQL data, the work-order queue, or backup source-of-truth.

## Memory

64 GB unified is shared with macOS, GPU, apps, and any containers. Serving
configs must set explicit context and parallel limits. Do not autoload several
30B+ models.

Studio Ollama is the single runner for AI Lab chat and agents. The intended
LaunchAgent setting is `OLLAMA_MAX_LOADED_MODELS=1`, so a second Ollama tag
waits and the idle model unloads instead of both staying resident. The default
keep-alive is about five minutes. This env var is **not** on the live
`com.ai-lab.ollama` agent yet; applying it restarts Ollama and drops whatever
is loaded.

A notebook that calls `mlx_lm.load` allocates Metal memory in the kernel.
Ollama cannot see or evict that process. That notebook gets the Studio to
itself: no large agent run, and no second MLX load, until the kernel drops
the weights. Notebooks that only need a completion call Ollama on
`127.0.0.1:11434` so they share this cap. Chat and agents stay on the local
model the operator selected. They do not move to a frontier model because
MLX is busy.

## Storage

- General weights: configurable `AI_LAB_MODEL_ROOT` / Ollama library
- Antares: `~/.ai-lab/antares/antares-1b/` (+ CLI zip under `cli/`)
- Never download weights in `setup.sh` without a gated IWO

## Workers vs control plane

```text
M1 orchestrator --Tailscale--> Studio Ollama (:11434)
M1 UI / scripts  --Tailscale--> Studio Jupyter (:8888)
M1 orchestrator --Tailscale--> Studio worker (:8090)   # optional; not live
```

Live Studio Ollama listens on all interfaces (ADR 0041), so loopback, the
Studio LAN, and Tailscale share one process. Lab clients still use
`http://mac-studio:11434`. Do not publish port 11434. Jupyter stays on the
Studio Tailscale address.

## Jupyter as operator path

`scripts/studio-jupyter-exec.py` remains available (token never printed). Prefer
SSH (`stevengerhart@mac-studio`) for LaunchAgent and brew work now that F-015 is closed.

## Antares (FEAT-015)

Vulnerability-localization **terminal agent** (prefer 1B). Loopback completions
(`:8001`), Tailscale job helper (`:8002`), and mini `/antares` UI are live
(IWO-047–049). See [../runbooks/antares-vuln-localize.md](../runbooks/antares-vuln-localize.md).
