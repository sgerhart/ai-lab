# IWO-018 — Browser API key entry on the mini

**Status:** Complete  
**Priority:** P1  
**Effort:** S  
**Feature:** [FEAT-012](../features/FEAT-012-lab-site-and-secret-vault.md)

## Problem

Operators need to enter foundation model API keys without SSH or editing
files. Keys must never appear in Git or in GET responses.

## What To Build / Fix

- `/secrets` HTML UI
- `GET /v1/secrets/status`, `PUT/DELETE /v1/secrets/providers/{id}`
- `PUT /v1/secrets/usage-billed` authorization flag (ADR 0038)
- File store under `~/.ai-lab/secrets/` (mode 600) until Vault (ADR 0039)

## Out Of Scope

- Live OpenAI/Anthropic/Gemini HTTP adapters (follow-on)
- Vault `up` / unseal

## Acceptance Criteria

1. Authenticated browser can save/clear openai|anthropic|gemini keys
2. Status responses never include secret values
3. Unit tests pass; validate-repo OK
