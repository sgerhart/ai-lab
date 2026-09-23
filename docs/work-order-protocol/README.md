# Work Order Protocol (AI Lab adoption)

**Status:** Adopted for *implementation* Work Orders (ADR 0036).  
**Upstream:** [dentroio/work-order-protocol](https://github.com/dentroio/work-order-protocol)

AI Lab uses the Work Order Protocol as the **specification standard** for
bounded engineering work in Git. It does **not** replace:

- Features (`docs/features/`, `FEAT-*`)
- Historical phase records (`WO-000`–`WO-007`)
- Runtime jobs on `mac-mini` (Postgres UUIDs, LangGraph)

## Start here

1. Root [`AGENT_PROCESS.md`](../../AGENT_PROCESS.md)
2. Canonical template [`templates/WO-template.md`](../../templates/WO-template.md)
3. [Lifecycle mapping to runtime states](lifecycle-mapping.md)
4. [Risk tiers and deploy gates](risk-and-deploy-gates.md)
5. Upstream quickstart / creating / implementing docs (read upstream; do not
   duplicate the whole book here)

## Adoption level

| Level | AI Lab today |
|-------|----------------|
| 1 Human Work Orders | **Yes** — template + Closeout |
| 2 Agent-Assisted | **Yes** — `AGENT_PROCESS.md` + `AGENTS.md` |
| 3 CI-Gated | Partial — `validate-repo.sh` / CI; not full protocol lint yet |
| 4 Factory-Operated | **No** — Clarion/agentic-factory stays adjacent (ADR 0007) |

## Where new IWOs live

Prefer `docs/work-orders/IWO-NNN-short-title.md` and/or a GitHub issue created
from the Work order template. Link the Feature (`FEAT-*`) when applicable.

## First adoption IWO

[IWO-001 — Adopt Work Order Protocol](../work-orders/IWO-001-adopt-work-order-protocol.md)
