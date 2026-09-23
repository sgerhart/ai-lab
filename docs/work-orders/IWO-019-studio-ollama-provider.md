# IWO-019 — Studio Ollama provider on the mini router

**Status:** Complete (live verified 2026-09-23)  
**Priority:** P1  
**Effort:** S  
**Feature:** [FEAT-011](../features/FEAT-011-frontier-model-access.md), [FEAT-003](../features/FEAT-003-studio-worker-and-models.md)

## Problem

`/agents` routed `ollama` through FakeBackend even though Studio Ollama was live
on Tailscale (`llama3.2:3b`) and `STUDIO_OLLAMA_URL` was set on the mini.

## What To Build / Fix

- Allow Ollama base URL on loopback **or** Tailscale/MagicDNS (`mac-studio`)
- Wire `OllamaBackend` into `ModelRouter` when `STUDIO_OLLAMA_URL` is set
- List models from `/api/tags`; health reflects reachability
- Docs: FEAT-003/011 status; mini runbook env

## Out Of Scope

- Cloud provider live HTTP; Vault migrate; Jupyter changes

## Acceptance Criteria

1. From Air `/agents`, select `ollama` + `llama3.2:3b`, run completes with real text — **verified**
2. Unit tests cover URL allowlist (reject public hosts) — **pass**
3. No secrets in Git

## Closeout

- Live: chat reply + agent runs via Studio `llama3.2:3b`
- Follow-on: IWO-020 (tool loop protocol for live models)
