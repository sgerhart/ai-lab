# Antares vulnerability localization (Studio)

**Host:** `mac-studio`  
**Feature:** FEAT-015 / IWO-047  
**Weights:** never in Git

## Status (2026-09-24)

- Antares-1B downloaded to Studio `~/.ai-lab/antares/antares-1b/`.
- CLI zip at `~/.ai-lab/antares/cli/antares-cli.zip`.
- Transformers MPS load smoke passed.
- Still needed: streaming `POST /v1/completions` server (CLI contract;
  upstream docs use vLLM) + network-disabled sandbox (IWO-048).

## Prerequisites

1. Operator accepts the gated model on Hugging Face:
   [fdtn-ai/antares-1b](https://huggingface.co/fdtn-ai/antares-1b)
2. HF access token on Studio only: `~/.ai-lab/hf.token` (`chmod 600`).
3. Studio Jupyter reachable from mini (`~/.ai-lab/studio-jupyter.token`).
4. Prefer fixing [F-015](../security/findings/F-015-studio-ssh-auth-failure.md)
   (Studio SSH) for routine ops; Jupyter exec is the temporary path.

## Preflight (mini)

```bash
./scripts/antares-preflight.sh
./scripts/antares-preflight.sh --jupyter-preflight   # needs studio-jupyter.token
```

## Download 1B (gated)

From mini (uses Jupyter kernel on Studio):

```bash
VENV=$HOME/.ai-lab/venv-jupyter-exec
$VENV/bin/python scripts/studio-jupyter-exec.py \
  --exec-file scripts/_antares_download_cell.py
```

Writes under Studio `~/.ai-lab/antares/antares-1b/` and copies
`assets/antares-cli.zip` to `~/.ai-lab/antares/cli/`.

## Serve (OpenAI-compatible)

Antares CLI expects an OpenAI-compatible chat endpoint — not general Studio
chat. Exact serve command depends on MLX vs transformers; record the chosen
command in the host overlay after first success. Do not bind `0.0.0.0`.

## Agent loop

Use the Antares CLI against a **read-only** repo snapshot in a network-disabled
sandbox (IWO-048). Human reviews SARIF/JSON before any remediation (FEAT-007).

## Verify

- `~/.ai-lab/antares/DOWNLOAD_OK` exists on Studio
- CLI zip present under `~/.ai-lab/antares/cli/`
- No Antares weights under the `ai-lab` Git tree
