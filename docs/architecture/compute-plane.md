# Compute plane (Mac Studio)

**Host directory:** [`hosts/studio/`](../../hosts/studio/README.md)  
**Status:** Ollama + JupyterLab **live** on `mac-studio` (Tailscale). Studio
worker API (`:8090`) **not** running. SSH as `stevengerhart@mac-studio` works
from Air and mini ([F-015](../security/findings/F-015-studio-ssh-auth-failure.md) closed).

**Chip:** M5 Max (attested).

## Runs here

| Component | Live |
|-----------|------|
| Ollama | Yes — `llama3.2:3b` on Tailscale `:11434` |
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

If Ollama is bound only to Studio loopback, remote routing fails. Live lab uses
a Tailscale-scoped listen (deploy-time).

## Jupyter as operator path

`scripts/studio-jupyter-exec.py` remains available (token never printed). Prefer
SSH (`stevengerhart@mac-studio`) for LaunchAgent and brew work now that F-015 is closed.

## Antares (FEAT-015)

Vulnerability-localization **terminal agent** (prefer 1B). Loopback completions
(`:8001`), Tailscale job helper (`:8002`), and mini `/antares` UI are live
(IWO-047–049). See [../runbooks/antares-vuln-localize.md](../runbooks/antares-vuln-localize.md).
