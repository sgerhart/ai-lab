# Antares vulnerability localization (Studio)

**Host:** `mac-studio`  
**Feature:** FEAT-015 / IWO-047  
**Weights:** never in Git

## Status (2026-09-24)

- Antares-1B downloaded to Studio `~/.ai-lab/antares/antares-1b/`.
- CLI zip at `~/.ai-lab/antares/cli/antares-cli.zip`.
- Transformers MPS load smoke passed.
- Completions server live on Studio **loopback** `127.0.0.1:8001` (IWO-048;
  Mac stdlib/transformers path, not vLLM).
- `sandbox-exec` deny-network profile in `hosts/studio/antares-sandbox.sb`.
- Antares CLI installed (`uv tool install`); profile `lab-antares-1b`.
- Smoke: `antares query` on fixture CWE-78 → finding `app.py` (~11s).
- `/antares` UI on mini proxies Studio job server `:8002` (IWO-049).
- Still needed: LaunchAgents so completions/jobs survive Studio reboot.

## Prerequisites

1. Operator accepts the gated model on Hugging Face:
   [fdtn-ai/antares-1b](https://huggingface.co/fdtn-ai/antares-1b)
2. HF access token on Studio only: `~/.ai-lab/hf.token` (`chmod 600`).
3. Studio Jupyter reachable from mini (`~/.ai-lab/studio-jupyter.token`).
4. SSH as `stevengerhart@mac-studio` (F-015 closed). Jupyter exec remains optional.

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

## Serve (OpenAI-compatible completions)

Antares CLI needs streaming `POST /v1/completions` (not chat). On Studio:

```bash
# dry-run
./scripts/antares-completions-server.sh
# foreground (or LaunchAgent later)
AI_LAB_BIND_ADDRESS=127.0.0.1 ./scripts/antares-completions-server.sh --apply
```

Live process: `~/.ai-lab/antares/completions.pid` / `completions.log`.
Served model id: `antares-1b`. Do not bind `0.0.0.0`.

## Sandbox

```bash
./scripts/antares-sandbox-run.sh --repo /path/to/repo --apply -- /bin/ls
```

Uses `hosts/studio/antares-sandbox.sb` (`deny network*`).

## Agent loop

Prefer the mini UI (`/antares`) or CLI. Optional: wrap CLI under
`antares-sandbox-run.sh` (deny-network). Human reviews SARIF/JSON before any
remediation (FEAT-007).

## Verify

- `~/.ai-lab/antares/DOWNLOAD_OK` exists on Studio
- CLI zip present under `~/.ai-lab/antares/cli/`
- No Antares weights under the `ai-lab` Git tree

## A GitHub repository

The Security form accepts a `github.com` URL. The Studio job clones a shallow snapshot under `~/.ai-lab/antares/snapshots/` and reviews that copy. Leave the weakness class blank to let Antares select up to 50 classes for the repository. Name `CWE-78` or `CWE-78,CWE-89` for a narrower review. CWE stands for Common Weakness Enumeration. Each class id is a link; the name and short definition open in a popup. A private repository clones only when the Studio can already reach GitHub. Put no credential in the URL. The Air checkout stays the place you change code.

## After a review

On a finished run, a read-only coding review opens each cited file and records a line, a verdict, and a reason. The page hides the Antares file list until that detailed review is complete. **Review drafts** and **Push drafts to the repository** appear after it finishes. Each pushed order stays Draft and is marked **Source: Security Audit**. See IWO-070.

## CLI smoke (Studio)

```bash
export ANTARES_ENDPOINT=http://127.0.0.1:8001/v1/completions
export ANTARES_API_KEY=local-no-auth   # server has no auth today
antares query ~/.ai-lab/antares/fixture-cwe78 \
  --cwe CWE-78 --profile lab-antares-1b --format json \
  --output ~/.ai-lab/antares/runs/smoke-cwe78
```

Human must review SARIF/JSON before any remediation.
