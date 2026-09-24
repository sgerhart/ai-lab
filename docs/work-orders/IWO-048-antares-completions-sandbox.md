# IWO-048 — Antares completions server + sandbox runner

**Status:** Done  
**Priority:** P1  
**Effort:** M  
**Owner:** human (operator)  
**Feature:** [FEAT-015](../features/FEAT-015-antares-vuln-localization.md)  
**Risk tier:** P1  

## Problem

Antares-1B weights are on Studio (IWO-047), but the CLI needs streaming
`POST /v1/completions` and a network-disabled repo sandbox. Upstream docs assume
vLLM; Studio has no Docker/Colima. SSH as `stevengerhart@mac-studio` is OK (F-015 closed).

## Decision Context

- Completions: stdlib HTTP server + transformers/MPS (no new heavy deps in Git
  runtime on mini). Bind loopback by default; optional Tailscale IPv4.
- Sandbox: macOS `sandbox-exec` with deny-network profile (no Docker on Studio).
- CLI install: `uv tool install` from unzipped `antares-cli.zip` when authorized.
- Alternatives rejected: vLLM on Mac; binding `0.0.0.0`.

## What To Build / Fix

- `scripts/antares-completions-server.py` + wrapper `.sh` (dry-run / `--apply`)
- `hosts/studio/antares-sandbox.sb` + `scripts/antares-sandbox-run.sh`
- Unit test for completions JSON shaping (no GPU required)
- Docs: FEAT-015, runbook, architecture compute-plane
- Live: start server on Studio via Jupyter; smoke `/v1/completions`

## Out Of Scope

- Studio UI hook (IWO-049)
- Auto-remediation / exploit generation
- (Historical) Studio SSH username confusion — closed as F-015

## Acceptance Criteria

1. Dry-run prints bind/model paths without starting.
2. `/v1/models` and streaming `/v1/completions` respond for served name
   `antares-1b` (or configured id).
3. Sandbox runner refuses network (documented profile) and cleans temp snapshot.
4. No weights or HF tokens in Git.

## AI Lab gates

- **Host mutate?** Yes — Studio process start under Continue for FEAT-015 next
  step (2026-09-24). Bind not `0.0.0.0`.
- Jupyter path optional; SSH preferred for host ops.

## Closeout

- Verification evidence (2026-09-24):
  - Completions server on Studio `127.0.0.1:8001` — `/health` ok;
    `POST /v1/completions` returned shaped JSON (`serve_ok`).
  - `sandbox-exec` profile denies network (curl nonzero); `/bin/echo` allowed.
  - Unit: `tests.test_antares_completions_shape`.
- Host deploy performed? Yes via Jupyter (server pid under
  `~/.ai-lab/antares/completions.pid`). Bind loopback only.
- Follow-on live verify (same day): `uv tool install` Antares CLI on Studio;
  profile `lab-antares-1b` → `http://127.0.0.1:8001/v1/completions`;
  `antares query` on CWE-78 fixture found `app.py` (report.json/md/sarif).
- Follow-on: IWO-049 UI **done**. Residual: LaunchAgents for completions/jobs across reboot.
