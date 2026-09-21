# ADR 0027 — Initial secret store is Keychain plus gitignored env

- **Status:** Accepted
- **Date:** 2026-09-21
- **Supersedes:** open decision D-006 for the *initial* deploy

## Context

A dedicated Vault/1Password/SOPS workflow is not chosen. Secrets must not enter Git (ADR 0003).

## Decision

Until a later ADR:

- Store passwords, API tokens, and Tailscale auth keys in **macOS Keychain** (or equivalent) on the host that needs them.
- Materialize a **gitignored** `infrastructure/compose.local.env` (or `.env`) on the M1 at deploy time only.
- Do not reuse Clarion Vault credentials in this lab.

## Consequences

- `.env.example` and `compose.example.env` stay empty/placeholder.
- A shared secret manager later is a new ADR, not a silent compose change.
