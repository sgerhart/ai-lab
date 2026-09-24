# IWO-047 — Antares-1B on Studio (pull gated)

**Status:** Done (weights on Studio; completions server follow-on)  
**Priority:** P1  
**Effort:** M  
**Owner:** human (operator)  
**Feature:** [FEAT-015](../features/FEAT-015-antares-vuln-localization.md)  
**Risk tier:** P1  

## Problem

FEAT-015 needs Antares-1B weights on `mac-studio` behind an OpenAI-compatible
endpoint for the Antares CLI. Studio Ollama currently only serves
`llama3.2:3b`. Direct SSH to Studio from Air and mini fails (publickey).

## Decision Context

- Prefer **Antares-1B** (not 350M) on Studio.
- Weights never in Git; download to `~/.ai-lab/antares/` or HF cache on Studio.
- Serve via OpenAI-compatible HTTP (transformers/MLX/vLLM) — not general chat.
- Operator access path while SSH is broken: Studio Jupyter API
  (`scripts/studio-jupyter-exec.py`) using `~/.ai-lab/studio-jupyter.token` on mini.
- Record SSH failure as [F-015](../security/findings/F-015-studio-ssh-auth-failure.md).

## What To Build / Fix

1. `scripts/studio-jupyter-exec.py` — remote cell exec (token never printed)
2. `scripts/antares-preflight.sh` — Ollama tags + Jupyter preflight
3. Runbook: download 1B + CLI zip; serve endpoint; no auto-remediation
4. Live: install deps + download 1B when disk/network OK (Continue auth)

## Out Of Scope

- IWO-048 sandbox runner (next)
- Exploit generation / auto-remediation
- Committing weights or HF tokens

## Acceptance Criteria

1. Preflight reports disk free + package presence without secrets.
2. Antares-1B files present under Studio HF cache or `~/.ai-lab/antares/`.
3. OpenAI-compatible `/v1/models` (or documented serve command) responds.
4. No weights in Git.

## AI Lab gates

- **Host mutate?** Yes — Studio download via Jupyter under operator Continue
  (Antares listed as mini/studio next step).
- **SSH fix** is separate; do not invent keys.

## Closeout

- Verification evidence (2026-09-24):
  - HF token present on Studio (`~/.ai-lab/hf.token`); gated download succeeded.
  - Snapshot at `~/.ai-lab/antares/antares-1b/` (`model.safetensors` ~3.67 GB).
  - CLI zip copied to `~/.ai-lab/antares/cli/antares-cli.zip`.
  - Transformers load on Studio MPS + short `generate` smoke (`load_ok`).
- Host deploy performed? Yes via Jupyter exec (SSH later fixed — F-015 closed).
- Residual: Antares CLI wants streaming `POST /v1/completions` (validated with
  vLLM). Mac-native completions server + sandbox runner → IWO-048 / follow-on.
  Do not claim the CLI agent loop is live yet.
