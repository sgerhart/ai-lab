# ADR 0024 — Qdrant API key required on first deploy

- **Status:** Accepted
- **Date:** 2026-09-21
- **Supersedes:** open decision D-017

## Context

Compose already interpolates `QDRANT__SERVICE__API_KEY` and fails if unset. Turning the key off for “ease of first boot” would leave a loopback vector DB unauthenticated on a public-design repo.

## Decision

First M1 deploy **requires** a Qdrant API key in the gitignored compose env. The example file keeps a non-live placeholder. Do not commit the real key.

## Consequences

- `infrastructure/compose.example.env` stays placeholder-only.
- Clients (when written) must send the key. No client is deployed yet.
