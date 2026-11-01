# IWO-127 — Frontier Model Token Usage Telemetry & Cost Estimation

**Status:** Complete  
**Priority:** P1  
**Effort:** S  
**Owner:** operator  
**Feature:** FEAT-011  
**Services / Areas:** platform, docs

## Problem

Under FEAT-011 (Frontier model access and provider router), cloud model providers (OpenAI, Anthropic, Gemini) were wired to secret storage with strict disable-by-default gates (ADR 0038). However, while raw provider response objects returned token usage, the adapters left `usage["estimated_cost_usd"] = None` and did not standardize `total_tokens`. Furthermore, the control plane streaming route (`/v1/conversations/{id}/messages/stream`) did not emit an SSE `metrics` event for non-Ollama backends, preventing the UI and operators from receiving real-time token telemetry and dollar-cost accounting for frontier model requests.

## Decision Context

- **Chosen approach:**
  - Define `PROVIDER_MODEL_RATES` in `cloud_backends.py` capturing official input/output token pricing per 1M tokens for OpenAI (`gpt-4o-mini`, `gpt-4o`), Anthropic (`claude-3-5-haiku-latest`, `claude-sonnet-4-5`), and Google Gemini (`gemini-2.0-flash`, `gemini-1.5-pro`), along with robust provider-level fallbacks.
  - Implement `estimate_cost_usd(provider: str, model: str, input_tokens: int | None, output_tokens: int | None) -> float | None` with IEEE 754 precision rounding.
  - Standardize `total_tokens`, `input_tokens`, `output_tokens`, and `estimated_cost_usd` across `OpenAIBackend`, `AnthropicBackend`, and `GeminiBackend`.
  - In `control_app.py`'s `stream_message`, emit SSE `{"event": "metrics", ...}` for non-Ollama completions so the browser chat UI tracks token usage and expenditure live.
- **Constraints Preserved:**
  - Cloud providers remain strictly disabled by default (`usage_billed_not_authorized`).
  - No secrets ever echoed in responses or telemetry.
  - All tests use mocked HTTP responses; zero live network egress or charges in test suites.

## What Was Built

1. **`platform/src/ai_lab_platform/cloud_backends.py`**:
   - Added rate table `PROVIDER_MODEL_RATES` and estimation helper `estimate_cost_usd`.
   - Populated `total_tokens` and `estimated_cost_usd` in `OpenAIBackend.complete`, `AnthropicBackend.complete`, and `GeminiBackend.complete`.
2. **`platform/src/ai_lab_platform/control_app.py`**:
   - Emitted `event: metrics` in SSE stream on non-Ollama completions with `input_tokens`, `output_tokens`, `total_tokens`, and `estimated_cost_usd`.
3. **`tests/test_cloud_backends.py`**:
   - Verified token totals and cost estimation formulas for OpenAI, Anthropic, and Gemini.
   - Verified `estimate_cost_usd` behavior for exact matches, default fallbacks, unknown providers, and `None` arguments.
   - Added `test_stream_message_emits_cloud_metrics` asserting end-to-end SSE event dispatch.

## Acceptance Criteria

1. [x] Cloud backends return honest token counts and dollar cost estimates for all completions.
2. [x] Unknown models under known providers fall back gracefully to provider default rates.
3. [x] The SSE stream emits an `event: metrics` payload containing token usage and cost for frontier requests.
4. [x] Unit tests pass without any live network calls or expenditures.
5. [x] Full test suite and repo validation scripts pass cleanly.

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none
- **May run on Air?** Yes for unit tests.
