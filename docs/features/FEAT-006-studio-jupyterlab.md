# FEAT-006 — Studio JupyterLab and notebook experimentation

- **Status:** Specified
- **Created:** 2026-09-21
- **Owner:** human (operator)
- **GitHub issue:** [#7](https://github.com/sgerhart/ai-lab/issues/7)

## Purpose

Give the owner early, direct access to a **Studio-hosted JupyterLab** and Python
kernel for AI experimentation—independent of the mini agent harness.

**First milestone:** Air browser → Studio JupyterLab → cells execute on Studio.

**Later (separate):** optional durable experiment submit from a notebook to the
mini. Ordinary notebook cells must **not** route through the agent harness.

## User workflow (milestone 1)

1. Owner authorizes Studio host changes.
2. Managed Studio Python env with JupyterLab + named `ipykernel`.
3. Jupyter binds loopback; Air reaches it via **SSH tunnel** (+ auth token).
4. Open JupyterLab; run hardware/filesystem check cell.
5. Run one small repeatable inference/eval notebook; document artifact storage.

## Target host(s)

| Role | Host alias | Why |
|------|------------|-----|
| JupyterLab + kernel | `mac-studio` | Compute plane |
| Browser / SSH client | `mac-air` | Human plane |
| Optional later submit | `mac-mini` | Durable experiment API |

## Dependencies

- Studio on tailnet / SSH (host auth); does **not** require FEAT-010
- FEAT-003 helpful for local models inside notebooks

## Proposed deliverables

- Runbook: tunnel, token, env pin
- Sample notebook + artifact/versioning notes
- Later IWO: notebook → mini experiment submit (not milestone 1)

## Proposed implementation work orders

| ID | Title | Depends on | Acceptance |
|----|-------|------------|------------|
| [IWO-011](../work-orders/IWO-011-studio-jupyter-host.md) | Verify Studio + Tailscale | Owner host auth | Reachable |
| [IWO-012](../work-orders/IWO-012-jupyterlab-environment.md) | JupyterLab + ipykernel env | IWO-011 | Lab starts on loopback |
| [IWO-013](../work-orders/IWO-013-jupyter-ssh-tunnel.md) | SSH tunnel from Air | IWO-012 | Browser opens Lab |
| [IWO-014](../work-orders/IWO-014-jupyter-air-verify.md) | Hardware check from Air | IWO-013 | Proof cell on Studio |
| [IWO-015](../work-orders/IWO-015-jupyter-sample-notebook.md) | Sample AI notebook + artifacts | IWO-014 | Documented path |
| [IWO-064](../work-orders/IWO-064-jupyter-ollama-help.md) | Code help via Studio Ollama | Jupyter live | In progress. `notebook-intelligence` 6.0.0 on Studio. Air question not asked |

## Acceptance criteria

- [ ] Milestone 1: cell runs on Studio from Air browser
- [ ] Auth enabled; not exposed on `0.0.0.0`
- [ ] Notebook cells do not go through mini harness
- [ ] Artifact storage documented

## Out of scope

- Air as lab Jupyter *server*; forcing every cell into a runtime WO

## Implementation status (honest)

| Layer | Status | Evidence |
|-------|--------|----------|
| Spec | Done | this file |
| Code | Not started | — |
| Deploy | Not authorized | Studio not up |
| Live verified | No | — |
