# FEAT-012 — Lab site (frictionless Studio access) and secret vault

- **Status:** Partial (live on mini; Vault not up). The connection hub at `/lab` now redirects to the Studio at `/`. Jupyter opens from **Jupyter Labs** in that sidebar.
- **Created:** 2026-09-23
- **Owner:** human (operator)
- **Priority:** Core platform (post Studio bring-up)

## Purpose

Give the operator a **mini-hosted lab site** so Air browsers can use Studio
Jupyter, see compute health, and reach agents **without SSH tunnels or ad-hoc
CLI**. Store foundational model API credentials in a **Vault on the mini**
(not Git, not Clarion Vault) so FEAT-011 can enable usage-billed providers
safely.

## User workflow

1. Open the Studio over Tailscale (`/`). `/lab` and `/agents` redirect there.
2. Authenticate with the lab API token.
3. **Jupyter Labs** in the sidebar opens Studio Jupyter (no `ssh -L`).
4. See Studio Ollama / Jupyter / worker reachability.
5. (Follow-on) Configure / confirm OpenAI · Anthropic · Gemini keys in Vault;
   select them from `/agents` with billing class visible.

## Target host(s)

| Role | Host alias | Why |
|------|------------|-----|
| Lab site + Vault + router | `mac-mini` | Control plane |
| Jupyter + Ollama (Tailscale-scoped) | `mac-studio` | Compute |
| Browser | `mac-air` | Human plane |

## Dependencies

- FEAT-004 (UI shell), FEAT-006 (Studio Jupyter), FEAT-011 (providers)
- ADR 0034 (Tailscale bind), ADR 0038 (billing), **ADR 0039** (Vault)
- Studio already on Tailscale with Jupyter/Ollama running

## Proposed deliverables

- `/lab` connection hub HTML
- `/secrets` write-only API key entry UI
- `/v1/connect/status` (no secret values)
- Authenticated Jupyter open/redirect (token server-side only)
- Studio Jupyter stays on its Tailscale address. Studio Ollama listens on all interfaces (ADR 0041). Do not publish port 11434
- Compose Vault service (scaffold; deploy gated)
- Secret **names** for foundation APIs; values only in `~/.ai-lab/secrets/` or Vault / gitignored overlays

## Proposed implementation work orders

| ID | Title | Depends on | Acceptance |
|----|-------|------------|------------|
| [IWO-016](../work-orders/IWO-016-lab-site-connect-hub.md) | Lab site + connect status + Jupyter open | Studio Jupyter up | Air opens Lab via mini, no SSH |
| [IWO-017](../work-orders/IWO-017-vault-scaffold.md) | Vault compose scaffold + provider secret names | ADR 0039 | `compose config` with profile; no live keys in Git |
| [IWO-018](../work-orders/IWO-018-browser-api-key-entry.md) | Browser API key entry | IWO-016 | Keys saved; never echoed |

## Acceptance criteria

- [x] From Air: authenticated `/lab` → Studio Jupyter without manual SSH tunnel
- [x] Connect status shows Studio Jupyter/Ollama reachability from mini
- [x] No secrets in Git or HTML responses
- [x] Vault not required for Jupyter path; required before enabling paid APIs

## Out of scope

- Full Jupyter reverse-proxy WebSocket gateway (v1 uses Tailscale direct + token redirect)
- Enabling paid API calls (separate owner authorization)
- Reusing Clarion Vault credentials (ADR 0025 / 0039)

## Implementation status (honest)

| Layer | Status | Evidence |
|-------|--------|----------|
| Spec | Done | this file |
| Code | Done | IWO-016–018 in Git |
| Deploy | Partial | Studio `/`, secrets, and help live on mini; Vault not `up` |
| Live verified | Partial | Jupyter opens from the Studio sidebar; keys UI write-only |
