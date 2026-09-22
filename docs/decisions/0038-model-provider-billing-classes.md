# ADR 0038 — Model provider billing classes and subscription boundaries

- **Status:** Accepted
- **Date:** 2026-09-21
- **Related:** ADR 0016, 0019, 0027; FEAT-011

## Context

Operators often assume ChatGPT Plus/Pro, Claude Pro/Max, or Google AI
subscriptions include generic API inference for a custom background harness.
Official documentation says otherwise. Misuse risks unexpected charges or ToS
violations.

## Decision

### Billing classes (required labels)

Every selectable model in AI Lab UI/API must declare exactly one class:

| Class | Meaning |
|-------|---------|
| `local` | Studio Ollama/MLX or optional mini model; no cloud token billing |
| `subscription_client` | Official supported client product (e.g. Claude Code / Codex) used **as that product**, not as a silent API for the harness |
| `usage_billed_api` | Platform API keys (OpenAI, Anthropic Console, Gemini API, etc.) |

### Subscription findings (2026-09-21)

- **OpenAI:** ChatGPT Plus/Pro does not include API credits; API is billed
  separately ([OpenAI Help — ChatGPT Plus](https://help.openai.com/en/articles/6950777-what-is-chatgpt-plus)).
- **Anthropic:** Claude Pro/Max does not include Console/API
  ([Anthropic Help](https://support.claude.com/en/articles/9876003-i-have-a-paid-claude-subscription-pro-max-team-or-enterprise-plans-why-do-i-have-to-pay-separately-to-use-the-claude-api-and-console)).
  Claude Code may use Pro/Max for supported Claude Code workflows; setting
  `ANTHROPIC_API_KEY` bills the API instead.
- **Google:** Consumer Google AI / Gemini plans do not pay for arbitrary
  external Gemini API apps; API key usage is billed via AI Studio / Cloud
  Billing ([Google AI plans](https://ai.google.dev/gemini-api/docs/google-ai-plans)).

### Harness rules

1. Cloud providers start **disabled** until the owner configures credentials and
   explicitly accepts billing implications.
2. **No silent fallback** from `local` to `usage_billed_api`.
3. Do not scrape consumer chat UIs, extract session cookies, reverse-engineer
   private endpoints, or abuse coding CLIs as unsupported general APIs.
4. Credentials stay in Keychain / gitignored env (ADR 0027); never sent to browsers.
5. Live chargeable tests and account purchases require **separate** human
   authorization beyond accepting an IWO.

## Consequences

- FEAT-011 implements the router against these classes.
- UI (FEAT-004) must display the class next to every model choice.

## Alternatives considered

- Treat Plus/Pro as API — rejected; contradicts vendor docs.
- Cloud-only default — rejected for a local-silicon lab.
