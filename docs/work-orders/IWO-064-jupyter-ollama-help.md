# IWO-064 — Jupyter code help via Studio Ollama

**Status:** In progress (Notebook Intelligence 6.0.0 installed on the Studio; Air chat question not yet asked)  
**Priority:** P2  
**Effort:** M  
**Owner:** human (operator)  
**Feature:** [FEAT-006](../features/FEAT-006-studio-jupyterlab.md)  
**Services / Areas:** hosts, docs

## Problem

Studio JupyterLab is live (`~/.ai-lab/jupyter/.venv` on `mac-studio`, token auth, Tailscale bind). The venv can call Studio Ollama and can load MLX in the kernel. Nothing in the Lab UI answers a coding question.

The operator will use notebooks for small, educational models. Coding help and questions inside Jupyter should call the same Ollama the lab chat and agents already use. They should not load a second large model with MLX, and they should not go through the mini harness or a frontier API.

## Decision Context

- Chosen approach: Install [Notebook Intelligence](https://pypi.org/project/notebook-intelligence/) in the Studio Jupyter venv. Point its chat provider at Ollama on `127.0.0.1:11434` and an already installed tag, `qwen3-coder:30b`. Pin that in the Jupyter start environment with `NBI_CHAT_MODEL_PROVIDER=ollama` and `NBI_CHAT_MODEL_ID=qwen3-coder:30b`. Ollama on the Studio already answers loopback. The first question loads the tag. It unloads about five minutes after the last request.
- Alternatives rejected: The current Jupyter AI extension, which shells out to external agents (Claude, Codex, Copilot). Loading an MLX model as the assistant. Routing the question through the mini Coding Assistant. A silent switch to a frontier model when another model is resident.
- Assumptions: `qwen3-coder:30b` remains installed on Studio Ollama. Jupyter keeps running on the Studio, not the Air. Notebook experiments may still call `mlx_lm.load` for a small model. That is the lesson, not the assistant.
- Open decisions:
  - Inline autocomplete stays off in this slice (`NBI_INLINE_COMPLETION_MODEL_PROVIDER=none`). A 30B tag on every keystroke is the wrong shape. A later slice can turn it on only after the operator authorizes a small coder tag.
  - Accepting this IWO does not apply `OLLAMA_MAX_LOADED_MODELS=1`. That cap is already written in the Studio runbook and still needs its own restart authorization.

## What To Build / Fix

Git, before any host change:

- `hosts/studio/start-jupyterlab.sh.example` exports the NBI chat provider and model id above, sets the inline-completion provider to `none`, and does not set a cloud API key or Claude mode.
- `docs/runbooks/studio-jupyter-from-air.md` states how help works: ask in the Notebook Intelligence chat panel; the call is Ollama on the Studio; a small MLX load in a cell is a separate, educational model; restart that kernel when the lesson is done if an agent run needs the memory.

Studio, only after a separate authorization in the conversation:

- `pip install` Notebook Intelligence into `~/.ai-lab/jupyter/.venv`. Record the installed version in the runbook. Do not `ollama pull`.
- Restart JupyterLab with the updated start script so the env pins apply.
- From the Air, open Jupyter through the lab site and ask one coding question. The reply must come from `qwen3-coder:30b`. Status Dashboard **In memory** shows that tag while it is resident.

## Expected Change Surface

- Expected: start-script example, Jupyter runbook, this IWO’s closeout after the live check
- Tests: `./scripts/validate-repo.sh`. No new platform unit test; the assistant is a Jupyter extension configured on the Studio
- Docs/status: FEAT-006 row in `docs/features/index.md` after the live check, not before

## Out Of Scope

- `OLLAMA_MAX_LOADED_MODELS=1` and an Ollama restart
- A probe that reports MLX residency on the Status Dashboard
- Pulling a smaller coder model for ghost-text autocomplete
- Notebook Intelligence agent mode that edits files or runs cells on its own
- Claude mode, Copilot sign-in, or any frontier key in the Jupyter environment
- Changing the mini Coding Assistant, its worktree, or its approval gate
- Routing a notebook cell through the mini harness

## Do NOT Change

- Jupyter bind stays the Studio Tailscale address or `127.0.0.1`. Never `0.0.0.0`
- Token auth stays on. The token stays out of Git
- Ordinary notebook cells do not go through the mini
- No silent fallback from local Ollama to a usage-billed model
- No model pull and no secret in the start script
- Accepting this IWO does not authorize the Studio install or the Jupyter restart

## Acceptance Criteria

1. [x] The start-script example pins chat to Ollama `qwen3-coder:30b` and pins inline completion to `none`.
2. [x] The runbook tells the operator that coding help calls Ollama, and that a small educational MLX load is not that help.
3. [ ] After the separate Studio authorization: one coding question asked in Jupyter on the Air is answered by `qwen3-coder:30b`, and `/api/ps` on the Studio lists that tag.
4. [x] `./scripts/validate-repo.sh` passes.
5. [ ] Closeout records the installed Notebook Intelligence version and whether the live question was asked. Until that authorization, host deploy performed is No.

## Validation Plan

- Automated: `./scripts/validate-repo.sh` on the Git change
- Manual (only after Studio authorization): open Jupyter from the lab site on the Air, ask one code question, confirm the model on the Studio with `curl -sS http://127.0.0.1:11434/api/ps`
- Evidence to include: extension version, the model name from `/api/ps`, and that no pull was run

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** **No** — installing into `~/.ai-lab/jupyter/.venv` and restarting JupyterLab need a separate human authorization
- **Privileged tools expected?** none
- **May run on Air?** No — the browser on the Air opens Studio Jupyter. Do not install this extension on the Air

## Execution

- **Branch:** `iwo/064-jupyter-ollama-help`
- **Risk tier:** P1 — the extension runs inside Jupyter, whose root is the Studio home directory
- **Pre-PR / pre-merge gate:** `./scripts/validate-repo.sh`
- **Depends on:** Jupyter already live on `mac-studio` (IWO-011–015). Studio Ollama tags include `qwen3-coder:30b`
- **Human verification required:** Yes
- **Reviewer / approver:** operator
- **Project status record:** `docs/features/index.md` and this file
- **Other status surfaces:** [FEAT-006](../features/FEAT-006-studio-jupyterlab.md)

## Closeout

- Verification evidence: 2026-09-25 on `mac-studio`. `notebook-intelligence==6.0.0` and `mcp==1.30.0` in `~/.ai-lab/jupyter/.venv`. JupyterLab 4.6.4. LaunchAgent `com.ai-lab.jupyterlab` restarted. Capabilities: chat `ollama` / `qwen3-coder:30b`, inline provider `none`. Startup talked to Ollama `/api/tags` and `/api/show`. `/api/ps` listed no model. No `ollama pull`.
- Follow-ons filed: none. One coding question from the Air browser is still open.
- Residual risks: the package ships a Claude CLI and Copilot/OpenAI provider entries. This process does not enable them. Inline completion's stored model id can still read `gpt-4o-copilot` while its provider is `none`, so it does not call out. Restarting Jupyter stopped the kernel that was already running.
- Docs/status updated: runbook records 6.0.0. 5.3.1 could not import.
- Status surfaces reconciled: features index and work-orders README
- Summary metadata reviewed: yes
- Planning-only change? No
- Host deploy performed? Yes — venv install and Jupyter LaunchAgent restart on `mac-studio`. No model pull. `OLLAMA_MAX_LOADED_MODELS` was not changed.
