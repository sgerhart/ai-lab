# ADR 0017 — Agent execution isolation

- **Status:** Accepted
- **Date:** 2026-09-20

## Context

Development agents will touch git checkouts. Research agents will fetch URLs. A Docker container on macOS shares the host kernel via a Linux VM and is **not** a boundary for malware analysis.

## Decision

Isolation tiers:

| Tier | Use | Mechanism |
|------|-----|-----------|
| 0 | Read-only lab ops, docs | Process on the Air or M1, no tools that write |
| 1 | Bounded development in a specified repo | Workspace directory allowlist; no host-wide FS |
| 2 | Untrusted dependency install / code exec | Dedicated directory + container **if** the task is still trusted-lab |
| 3 | Hostile / malware analysis | **Out of scope.** Separate future system, not this repo |

No agent gets silent host-wide privileges. Tool allowlists are per work order. VM isolation is documented as a future option, not implemented now.

## Consequences

- This repo will not ship a malware-analysis lab.
- Development agent GitHub access is scoped (no org-wide tokens in the agent env).

## Alternatives considered

- "Just use Docker" as a security story — rejected for hostile code.
- Full VM per job on day one — too much ops; deferred.
