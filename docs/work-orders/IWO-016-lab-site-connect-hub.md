# IWO-016 — Lab site connect hub (frictionless Studio Jupyter)

**Status:** Complete  
**Priority:** P1  
**Effort:** M  
**Owner:** human + agent  
**Feature:** [FEAT-012](../features/FEAT-012-lab-site-and-secret-vault.md)  
**Services / Areas:** platform, docs, hosts/studio

## Problem

Studio Jupyter works but Air access requires `ssh -L` and token CLI. That
friction blocks everyday use of the Studio GPU/MLX/Ollama setup.

## Decision Context

- Chosen approach: Mini `/lab` hub + authenticated redirect to Studio Jupyter
  over Tailscale (Studio binds Jupyter to Tailscale IPv4, not `0.0.0.0`).
- Alternatives rejected: Full WS reverse proxy on mini (later); keep SSH-only.
- Assumptions: MagicDNS name `mac-studio` resolves on the tailnet.
- Open decisions: Whether mini later proxies Jupyter WebSockets (follow-on).

## What To Build / Fix

- `GET /lab` connection hub
- `GET /v1/connect/status` (reachability; no secrets)
- `GET /v1/connect/jupyter` authenticated redirect with server-side token
- Settings: `STUDIO_JUPYTER_URL`, `STUDIO_OLLAMA_URL`, token file path
- Update Studio Jupyter/Ollama start to prefer Tailscale IPv4 bind
- Tests for status + auth gate; docs/runbook

## Expected Change Surface

- Expected: `platform/`, `docs/`, Studio start script / runbook
- Tests: `tests/test_lab_connect.py`
- Docs/status: FEAT-012, features index, studio Jupyter runbook

## Out Of Scope

- Vault deploy / unseal (IWO-017)
- Enabling paid cloud providers
- Changing Tailscale ACLs

## Do NOT Change

- No secrets in Git; no `0.0.0.0` binds; no Clarion Vault reuse

## Acceptance Criteria

1. `GET /lab` serves HTML with Studio connection actions
2. Without token (when configured): `/v1/connect/jupyter` → 401
3. With token + configured URL: redirect to Studio Jupyter
4. `./scripts/validate-repo.sh` and unit tests pass

## AI Lab gates

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none
- **May run on Air?** Yes (docs/code); Studio bind change needs separate auth

## Closeout

- Verification evidence: Air → `http://mac-mini:8088/lab` → Open Jupyter (Tailscale;
  no `ssh -L`). `/v1/connect/status` shows Studio Jupyter + Ollama.
- Auth: `AI_LAB_AUTH_MODE=trusted_tailnet` (no bearer paste on tailnet).
