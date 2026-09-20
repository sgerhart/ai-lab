# ADR 0003 — Secrets and artifacts stay out of Git

- **Status:** Accepted
- **Date:** 2026-09-19
- **Phase:** 0

## Context

An AI lab accumulates API keys, SSH identities, Vault tokens, GGUF weights, and datasets. This repository's GitHub remote is currently public. Even if it becomes private, Git history is a poor secret store.

## Decision

Git may contain:

- Secret *names* and rotation policy
- `.env.example` with empty placeholders
- Model catalog entries (name, license, size, backend)

Git must not contain:

- Secret *values*, private keys, kubeconfigs, `.env` files with values
- Model weights, checkpoints, or embeddings databases
- Raw datasets or database dumps
- Local overlays with IPs, MACs, serials, or SSH targets

Enforced by `.gitignore` and `scripts/validate-repo.sh`.

## Consequences

- Operators keep a gitignored overlay or a secret store for live values.
- Pulling a model is a host operation, not a Git operation.
- Accidental secret files are a security incident, not a commit to fix later.
