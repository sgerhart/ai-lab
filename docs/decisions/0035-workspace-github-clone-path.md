# ADR 0035 — Operator clone path is `~/workspace/github/<account>/<repo>`

- **Status:** Accepted
- **Date:** 2026-09-21
- **Related:** ADR 0002, ADR 0007, ADR 0022

## Context

The operator keeps Git working copies under `$HOME/workspace/github/`, with one subdirectory per GitHub account. This lab is `sgerhart/ai-lab`. A sibling account directory holds other working copies and must stay out of this repository (ADR 0007).

The Air already uses that layout (`/Users/stevengerhart/workspace/github/sgerhart/ai-lab`). The mini operator home is **`sgerhart`**, so the clone belongs at `/Users/sgerhart/workspace/github/sgerhart/ai-lab`. A first M1 clone was placed under `/Users/steve/` because SSH as `steve` worked first; that is the wrong home.

Air login `stevengerhart` and mini login `sgerhart` are the operator. Mini login `steve` is a second local account, not the workspace owner.

## Decision

On every lab Mac, clone (or relocate) this repo to:

```text
$HOME/workspace/github/sgerhart/ai-lab
```

Do not clone into `$HOME/ai-lab`, `$HOME/workspace/github/` (account root), or a sibling account directory.

Account subdirectory names and other repos stay in gitignored overlays. Do not invent a second GitHub org in committed files.

## Consequences

- Runbooks use `~/workspace/github/sgerhart/ai-lab`.
- Studio, when authorized, uses the same path for that host's home.
- Relocating a live M1 checkout requires updating `~/.ai-lab/start-control-plane.sh` and recreating compose from the new path (named volumes stay).
