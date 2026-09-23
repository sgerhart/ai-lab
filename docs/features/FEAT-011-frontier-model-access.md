# FEAT-011 — Frontier model access and provider router

- **Status:** Partial (Ollama live; cloud adapters gated — IWO-021)
- **Created:** 2026-09-21
- **Priority:** Core platform (with FEAT-010)
- **Owner:** human (operator)
- **GitHub issue:** [#12](https://github.com/sgerhart/ai-lab/issues/12)

## Purpose

Provide a **provider-neutral model router** so personal agents on the mini can
use Studio Ollama/MLX, an optional small mini model, or properly authorized
cloud APIs—with honest billing labels, no silent paid fallback, and credentials
that never reach the browser.

## Official subscription vs API (investigated 2026-09-21)

| Provider | Consumer / client subscription | Unattended harness API |
|----------|--------------------------------|-------------------------|
| OpenAI | ChatGPT Plus/Pro is **ChatGPT app** access. [Help: Plus](https://help.openai.com/en/articles/6950777-what-is-chatgpt-plus) states API usage is **separate and billed independently**. | Requires OpenAI **platform API key** + API billing. Do not scrape ChatGPT or reuse session cookies. |
| Anthropic | Claude Pro/Max is **Claude app** experience. [Help](https://support.claude.com/en/articles/9876003-i-have-a-paid-claude-subscription-pro-max-team-or-enterprise-plans-why-do-i-have-to-pay-separately-to-use-the-claude-api-and-console): subscription does **not** include Console/API. Claude Code may use Pro/Max for **supported Claude Code workflows**; `ANTHROPIC_API_KEY` routes to **API billing**. | Generic background agents need Console API keys + owner-accepted billing. |
| Google | Google AI / Gemini consumer plans apply to Gemini products / AI Studio UI quotas. Direct Gemini **API** use is billed via AI Studio / Cloud Billing separately ([Google AI plans note](https://ai.google.dev/gemini-api/docs/google-ai-plans): API key / external apps billed separately). | Optional Gemini adapter; disabled until configured. |

**Rule:** Generic unattended personal agents use **local models** or **usage-billed API** credentials the owner explicitly enables. Do not extract session credentials, scrape consumer UIs, reverse-engineer private endpoints, or turn coding CLIs into unsupported general-purpose APIs.

## Billing classes (UI must show)

1. **local** — Studio Ollama/MLX or optional mini model (no cloud $)
2. **subscription-authorized client** — supported official client workflows only (e.g. Claude Code / Codex where used as those products)—**not** the mini harness default path
3. **usage-billed API** — OpenAI / Anthropic / Gemini platform APIs

No silent switch from local → paid API.

## User workflow

1. Owner configures providers in gitignored env / Keychain (ADR 0027); accepts billing for API providers.
2. Cloud providers remain **disabled** until enabled.
3. Per agent or task, select provider/model; UI shows class + health.
4. Router records tokens/usage and estimated cost when the provider exposes it.
5. Timeouts, retries, cancellation, rate limits, concurrency caps apply.

## Target host(s)

| Role | Host alias | Why |
|------|------------|-----|
| Router / policy / usage SoT | `mac-mini` | Control plane |
| Local inference | `mac-studio` (primary), optional mini | Heavy vs small models |
| Cloud egress | `mac-mini` (or Studio if policy says) | API calls when authorized |

## Dependencies

- Features: FEAT-010 (consumes router), FEAT-003 (Studio Ollama live)
- ADRs: 0016, 0019, **0038**

## Proposed deliverables

- `ModelProvider` interface + FakeBackend (tests)
- Adapters: Ollama, optional mini, OpenAI, Anthropic, optional Gemini
- Health checks; fallback policy (explicit only)
- Redacted traces; scoped credentials
- UI labels for billing class

## Proposed implementation work orders

| ID | Title | Depends on | Acceptance (sketch) |
|----|-------|------------|---------------------|
| [IWO-004](../work-orders/IWO-004-model-router.md) | Router + Fake + disabled cloud stubs | ADR 0038 | Unit tests; no live $ |
| [IWO-021](../work-orders/IWO-021-cloud-provider-adapters.md) | OpenAI + Anthropic from secret store | IWO-004, IWO-018 | Gate + mocked HTTP; no live $ in CI |
| [IWO-019](../work-orders/IWO-019-studio-ollama-provider.md) | Studio Ollama provider | FEAT-003 host | Health + Agents completion |
| IWO-004-d | Optional Gemini adapter | IWO-004 | Same disable-by-default pattern |

## Acceptance criteria

- [x] Provider-neutral interface used by FEAT-010 loop
- [x] All cloud providers start disabled
- [x] UI shows local / subscription-client / usage-billed
- [x] No silent paid fallback
- [x] Secrets never in browser responses
- [x] No live chargeable tests without separate authorization

## Out of scope

- Creating paid accounts or buying credits from this repo
- Scraping ChatGPT / Claude.ai / Gemini web UIs
- Using Plus/Pro/Max as if they were API keys for the harness

## Implementation status (honest)

| Layer | Status | Evidence |
|-------|--------|----------|
| Spec in Git | Done | this file |
| Code | Partial: Ollama live; OpenAI/Anthropic adapters gated (IWO-021); Gemini stub | `cloud_backends.py` |
| Host deploy | Cloud off until `/secrets` authorize + keys | — |
| Live verified | Partial | Studio Ollama; cloud not live-charged |

## Notes

ADR 0038 records billing classes and subscription findings.
