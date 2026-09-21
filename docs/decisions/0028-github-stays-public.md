# ADR 0028 — GitHub remote stays public

- **Status:** Accepted
- **Date:** 2026-09-21
- **Supersedes:** open decision D-001

## Context

`github.com/sgerhart/ai-lab` is public (F-002). The owner chose to keep it public.

## Decision

The lab repository **remains public**. Visibility does not grant a copyright license (ADR 0021).

ADR 0005 still applies: do **not** commit IPs, MACs, serials, SSH URIs, Tailscale IPv4, or auth keys. Machine *names* the owner supplied (ADR 0032) may be committed.

## Consequences

- Treat the tree as readable by strangers. No secrets in Git.
- Making the repo private later is a new ADR plus a GitHub setting change (not done by agents unless asked).
