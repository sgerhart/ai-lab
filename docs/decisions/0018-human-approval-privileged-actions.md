# ADR 0018 — Human approval for privileged actions

- **Status:** Accepted
- **Date:** 2026-09-20

## Context

A development agent that can push, merge, deploy, or rewrite firewall rules is a privileged operator. Silent autonomy is how labs get ransomed by prompt injection.

## Decision

Work orders carry `approval_requirements`. Privileged tools (git push, gh merge, deploy, brew apply, compose up, restore, credential rotation, firewall, SSH config) transition the work order to `awaiting_approval` and must not execute until a human records approval.

The lab-operations agent is **read-only** in its initial policy file.

Irreversible restore over live volumes requires `--confirm-restore` and a typed backup id.

## Consequences

- Harness code implements the gate; UI on the Air is later.
- Audit events are stored with the work order (Postgres in production, SQLite in tests).

## Alternatives considered

- Trust the model — rejected.
- Approve every tool call including `grep` — too noisy; only privileged actions.
