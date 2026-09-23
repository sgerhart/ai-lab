# IWO-004 — Model router and billing classes

**Status:** Complete  
**Priority:** P1  
**Effort:** M  
**Owner:** operator  
**Feature:** [FEAT-011](../features/FEAT-011-frontier-model-access.md)  
**Risk tier:** P1 (credential handling; no live $ in this IWO)

## Problem

No provider-neutral router with honest billing classes. Ollama client and
FakeBackend exist in isolation.

## What To Build / Fix

- `ModelProvider` interface; FakeBackend; disabled OpenAI/Anthropic/(optional
  Gemini) stubs
- Health, timeout, retry, cancel hooks (unit-tested)
- Usage recording fields; no silent paid fallback
- UI/API labels: `local` | `subscription_client` | `usage_billed_api` (ADR 0038)

## Out Of Scope

Live chargeable calls; Studio Ollama bring-up; scraping consumer UIs

## Acceptance Criteria

1. Router selects FakeBackend in tests
2. Cloud providers disabled by default
3. Attempted silent fallback fails closed
4. No secrets in API responses

## AI Lab gates

- Host deploy? No
- Paid API live test? **Requires separate owner authorization**

## Depends on

IWO-002, ADR 0038


## Closeout

- Verification evidence: `tests.test_agent_loop` + validate-repo (2026-09-22)
- Host deploy performed? No
- Live mini migrate? No
