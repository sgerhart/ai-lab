# IWO-049 — Antares Studio UI / definition hook

**Status:** Done  
**Priority:** P1  
**Effort:** M  
**Owner:** human (operator)  
**Feature:** [FEAT-015](../features/FEAT-015-antares-vuln-localization.md)  
**Risk tier:** P1  

## Problem

Antares CLI smoke works on Studio (IWO-048), but operators have no Studio UI
path to launch a localize job or retrieve SARIF/JSON without SSH/Jupyter.

## Decision Context

- Add a dedicated `/antares` (or Agents sub-panel) page on the mini control
  plane that submits a **localize request** and shows last report artifacts.
- Execution: mini API triggers Studio via existing Jupyter/exec path **or**
  records a job + polls artifact dir — prefer API that shells out only on
  Studio when a Studio-side helper is reachable; otherwise queue metadata and
  document operator CLI fallback.
- Agent definition `vuln-localize` with **no write/remediation tools**.
- No auto-remediation; human reviews findings.

## What To Build / Fix

- Agent definition / policy stub `vuln-localize`
- Control-plane routes: start localize, status, fetch last report (read-only)
- Studio UI page linked from chrome nav
- Tests for API shaping (no live Antares required)
- Docs: FEAT-015, runbook

## Out Of Scope

- (none for SSH — F-015 closed)
- LaunchAgent for completions server (optional follow-on)
- Cloud Antares endpoints

## Acceptance Criteria

1. Operator can open Studio UI, submit CWE + repo path (or fixture default).
2. UI surfaces status + link/body for JSON/SARIF when a run completes.
3. Policy has no remediation/write tools.
4. Unit tests pass without Studio.

## AI Lab gates

- Host mutate only if starting Studio-side helper already authorized under
  FEAT-015 Continue path; prefer Git + mini UI first, live smoke if API can
  reach Studio completions/CLI.

## Closeout

- Verification evidence (2026-09-24):
  - `/antares` page 200 on mini; nav link in chrome.
  - Studio job server on Tailscale `:8002`; completions local `:8001`.
  - `POST /v1/antares/runs` CWE-78 → completed with finding `app.py`.
  - Unit: `tests.test_antares_ui`.
- Host deploy performed? Yes — job server on Studio; `ANTARES_JOB_URL` in mini
  start script; control plane restarted.
- Residual: LaunchAgents for completions/jobs (survive reboot).
