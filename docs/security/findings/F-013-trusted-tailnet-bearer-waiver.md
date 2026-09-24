# Finding F-013 — Tailnet peer waiver skipped application auth

- **Date:** 2026-09-24
- **Severity:** Medium
- **Component:** `platform/src/ai_lab_platform/auth.py`

## What happened

In `trusted_tailnet` mode, `require_auth` accepted requests from Tailscale CGNAT
(`100.64.0.0/10`) and loopback **without** a bearer token when
`AI_LAB_API_TOKEN` was set. Requests were also allowed when no token was
configured at all (open gate).

## Mitigation (Git)

- Bearer is always required when a token is configured (all modes).
- Missing token configuration fails closed (`api_token_not_configured`).
- `peer_trusted` remains informational on `/v1/auth/status` only.
- `auth.py` no longer depends on FastAPI imports (CI stdlib discover safe).

## Status

Mitigated in Git 2026-09-24. Deploy to mini still required for live effect.
