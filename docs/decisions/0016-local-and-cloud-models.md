# ADR 0016 — Local and cloud model support

- **Status:** Accepted
- **Date:** 2026-09-20

## Context

Agents will need local Studio models for private work and optional cloud models for overflow or capabilities not served locally. Forcing a single vendor would paint the harness into a corner.

## Decision

The platform exposes a **provider-neutral** model interface (completion, embed, rerank). Backends:

- Local Ollama on the Studio (initial)
- MLX-LM native (compute plane; not required for the first harness slice)
- Cloud providers via env-configured API keys (never in Git)

Not every agent uses the same model. Routing is a control-plane policy on the M1; bytes are inferred on the Studio or in the cloud.

Private data default: local. Cloud calls require the work order to allow `network:cloud-llm`.

## Consequences

- OpenAI/Anthropic keys are optional and gitignored.
- LangGraph (or any orchestrator) must call this interface, not a vendor SDK, if it is adopted later.

## Alternatives considered

- Local only forever — too rigid.
- Cloud only — rejected for a lab whose point is local silicon.
