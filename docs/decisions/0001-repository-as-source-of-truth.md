# ADR 0001 — Repository as source of truth

- **Status:** Accepted
- **Date:** 2026-09-19
- **Phase:** 0

## Context

Personal AI work is already happening on the operator workstation and adjacent lab systems. Facts about hosts, models, agents, and exposure currently live in SSH config, Docker state, product repos, and chat. That cannot be operated, reviewed, or handed to another agent.

## Decision

The `ai-lab` Git repository is the authoritative source of truth for the personal AI compute and agent environment. If a host, model, agent, network exception, or secret *name* is part of the lab, it is described here.

## Consequences

- Architecture changes require an ADR.
- Chat and product-repo notes are not canonical.
- Later automation (inventory scripts, compose, health checks) must read from this tree rather than invent a parallel store.
