# IWO-020 — Live Studio Ollama agent tool loop

**Status:** Complete (live verified 2026-09-23)  
**Priority:** P1  
**Effort:** S  
**Owner:** operator  
**Feature:** [FEAT-010](../features/FEAT-010-mini-personal-agent-loop.md), [FEAT-003](../features/FEAT-003-studio-worker-and-models.md)  
**Risk tier:** P1  
**Services / Areas:** platform, docs

## Problem

Chat with Studio Ollama works. The durable **agent loop** (`Run loop`) used a
weak `system=agent=…` prompt and a strict `TOOL`/`FINAL` parser tuned for
FakeBackend. Live models answered in prose → `FINAL` with **zero tools**.

## Decision Context

- Chosen approach: policy-aware TOOL/FINAL prompt; tolerant parser; prefer FINAL
  when both appear; stop repeating the same tool name.
- Alternatives rejected: native Ollama tools API (follow-on).
- Assumptions: `lab-operations` read-only tools for first live smoke.

## What To Build / Fix

- `agent_loop.py`, `ollama_backend.py` system field, `/agents` run summary UI
- Unit parser tests; live smoke on mini

## Out Of Scope

Cloud providers; privileged tools; native Ollama tools API; Vault

## Acceptance Criteria

1. Unit tests parse freeform TOOL/FINAL — **pass**
2. Live Run loop: ≥1 `tool_result` then complete — **verified** (`health_read`→FINAL)
3. Disallowed tools never execute — existing tests
4. validate-repo — **pass**

## Closeout

- Evidence: 2026-09-23 `backend=ollama` `llama3.2:3b`
  `kinds=['model_call','tool_result','model_call','final']`
- Host deploy: scp + LaunchAgent kickstart (this session)
- Schema migrate: No
