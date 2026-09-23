# ADR 0039 — HashiCorp Vault on the mini for lab secrets

- **Status:** Accepted
- **Date:** 2026-09-23
- **Supersedes:** ADR 0027 for *shared lab secrets and foundation-model API keys*
- **Related:** ADR 0003, 0016, 0025, 0038; FEAT-011, FEAT-012

## Context

ADR 0027 stored initial secrets in macOS Keychain plus gitignored compose env.
That remains valid for bootstrap passwords. Foundational model API keys and a
shared Jupyter open-token need a **lab-owned secret manager on the mini** so
the control plane and FEAT-011 router can read them without putting values in
Git or the browser.

Clarion/agentic-factory Vault instances stay **adjacent** (ADR 0025). Do not
reuse their tokens, unseal keys, or policies.

## Decision

1. Run **HashiCorp Vault** as an optional Compose service on **mac-mini**
   (profile `vault`), bound to loopback or this host's Tailscale IPv4
   (ADR 0034) — never `0.0.0.0`.
2. KV v2 mount path (convention): `secret/ai-lab/` with names such as
   `providers/openai`, `providers/anthropic`, `providers/gemini`,
   `studio/jupyter_token`.
3. Until Vault is initialized and unsealed on a live mini, continue using
   gitignored env / Keychain (ADR 0027) for compose DB passwords.
4. The control plane may read secrets via Vault HTTP API or a short-lived
   materialization into a gitignored file — **never** log or return values to
   `/lab` or `/agents`.

## Consequences

- New compose profile and docs; `compose up` without the profile unchanged.
- Enabling `usage_billed_api` providers still requires explicit owner
  authorization and billing acceptance (ADR 0038).
- Init/unseal/backup of Vault is an operator runbook, not bootstrap defaults.

## Alternatives rejected

- Only Keychain forever — poor multi-process sharing for the API.
- 1Password Connect first — fine later; Vault matches existing adjacent ops
  familiarity without copying Clarion credentials.
- SOPS-only — good for files; weaker for runtime API key rotation by the router.
