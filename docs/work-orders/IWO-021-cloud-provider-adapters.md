# IWO-021 — OpenAI / Anthropic adapters from secret store

**Status:** Complete (unit-verified; no live $)  
**Priority:** P1  
**Effort:** M  
**Owner:** operator  
**Feature:** [FEAT-011](../features/FEAT-011-frontier-model-access.md)  
**Risk tier:** P1  
**Services / Areas:** platform, docs

## Problem

Cloud providers were `DisabledCloudBackend` stubs even when keys exist under
`~/.ai-lab/secrets/` and usage-billed authorization is set on `/secrets`.

## What shipped

- `cloud_backends.py` — OpenAI Chat Completions + Anthropic Messages
- Enabled only when `usage_billed_authorized` **and** provider key present
- Gemini remains stub
- Agent-run gate allows usage_billed when authorize + key
- Tests: gate + mocked HTTP (no live chargeable calls)

## Acceptance Criteria

1. Without authorize: enabled=false; complete → PermissionError — **pass**
2. Authorize + key + mocked HTTP → text — **pass** (skipped on hosts without httpx)
3. No secrets in status/models — **pass**
4. validate-repo — **pass**
5. No live paid API in automated tests — **pass**

## Closeout

- Evidence: `tests.test_cloud_backends` 2026-09-23
- Host deploy: scp + kickstart (this session)
- Live chargeable call: **No** — owner must paste keys + check authorize on `/secrets`
