# ADR 0036 — Adopt Work Order Protocol for implementation contracts

- **Status:** Accepted
- **Date:** 2026-09-21
- **Related:** ADR 0001, 0006, 0018, 0020; FEAT-001; IWO-001
- **Upstream:** [dentroio/work-order-protocol](https://github.com/dentroio/work-order-protocol)

## Context

AI Lab introduced Features (`FEAT-*`) and already has runtime work orders on the
M1 (Postgres + LangGraph). Implementation tasks still lacked the upstream Work
Order Protocol’s cold-start template and agent process. The GitHub issue
template was a short stub; `AGENT_PROCESS.md` and `templates/WO-template.md`
were missing.

## Decision

1. Adopt the Work Order Protocol as the **specification standard** for
   **implementation** Work Orders in this repository (Level 1–2).
2. Keep three entities distinct: Feature, Implementation Work Order, Runtime
   work order (see `docs/features/README.md` and
   `docs/work-order-protocol/lifecycle-mapping.md`).
3. Preserve AI Lab’s **stricter host-deployment approvals**: accepting an IWO
   never authorizes `--apply`, compose `up`, model pull, restore, or network
   changes without a separate human authorization
   (`docs/work-order-protocol/risk-and-deploy-gates.md`).
4. Do **not** rename historical `WO-000`–`WO-007` or replace the runtime
   `Status` enum with protocol lifecycle labels.

## Consequences

- Root `AGENT_PROCESS.md` and `templates/WO-template.md` are required reading
  for agents implementing IWOs.
- GitHub work-order issues use the expanded template.
- Factory Level 4 automation remains out of scope (adjacent stacks stay
  adjacent).

## Alternatives considered

- Use only Features and chat — rejected; not cold-start dispatchable.
- Make protocol statuses the Postgres schema — rejected; breaks ADR 0020 harness.
- Vendor the entire protocol documentation tree — rejected; link upstream.
