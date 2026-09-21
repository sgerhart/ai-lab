# ADR 0022 — sgerhart Git identity and `github-sgerhart` remote

- **Status:** Accepted
- **Date:** 2026-09-21
- **Supersedes:** open decision D-002

## Context

`git@github.com` on this workstation authenticates as `dentroio`. The lab remote is `sgerhart/ai-lab`. Commits for this repo must not use the Dentro address.

## Decision

- **Git author (this repo only):** `Steven Gerhart <sgerhart@gmail.com>` via `git config --local`.
- **Push URL:** `git@github-sgerhart:sgerhart/ai-lab.git` (SSH host alias, not the default `github.com` key).
- Do not change global `user.email` from this repository.

Existing commits that still show `steve@dentro.io` are historical. Rewriting them requires an explicit force-push request.

## Consequences

- `gh` active account may still be `dentroio`. Use the sgerhart SSH host for Git.
- Documented in `AGENTS.md`.
