# Features and future capabilities

**Status:** Capability record plus backlog. No feature here is authorized for implementation or deploy under this file alone.  
**Updated:** 2026-09-24

This tree holds **desired capabilities**. It is not the M1 Postgres work-order store, and it is not the historical phase checklist in [`../work-orders/`](../work-orders/README.md).

## Lifecycle

```text
Idea
  → feature specification (docs/features/)
  → proposed implementation work orders
  → human approval of the plan
  → implementation in Git
  → tests
  → pull request
  → human review / merge
  → explicit deployment authorization
  → live verification
  → completion recorded on the feature
```

Rules:

- A feature may spawn **many** implementation work orders.
- Implementation work orders do **not** auto-execute on hosts.
- Runtime work orders on `mac-mini` are a **separate** system (Postgres + FastAPI). Creating docs here must not create runtime jobs.
- Human approval is required before privileged tools, deploys, merges that publish, model pulls, or live restore. Agents must not self-approve.

## Three distinct entities

### 1. Feature

A **desired capability or user outcome**. Identified as `FEAT-NNN`. Lives in Git under `docs/features/`. May list multiple proposed implementation work orders. Status is about product intent and readiness, not Postgres rows.

### 2. Implementation work order

A **bounded engineering task** (design, code, tests, docs). Identified historically as `WO-000`…`WO-007` for phases 0–7, and as `IWO-…` (or GitHub issues from the Work order template) when tied to a feature. Shape follows the [Work Order Protocol](../work-order-protocol/README.md) (`templates/WO-template.md`, ADR 0036). Completing an implementation work order in Git is **not** host deploy.

Historical phase records `WO-000`–`WO-007` remain under [`../work-orders/`](../work-orders/README.md). Do not rename them or claim they are live PostgreSQL jobs.

### 3. Runtime work order

An **execution record** on the M1 control plane (`POST /v1/work-orders`). Durable state, attempts, approvals, artifacts. Managed by LangGraph + Postgres (ADR 0020). Operators submit these from the Air; they are not Markdown files in this tree.

| Concern | Feature | Implementation WO | Runtime WO |
|---------|---------|-------------------|------------|
| Home | `docs/features/` | `docs/work-orders/IWO-*` + GitHub WO issues | Postgres on `mac-mini` |
| ID | `FEAT-NNN` | `WO-NNN` / `IWO-…` | UUID |
| Approves | Human plan / PR / deploy auth | Human review of code | Human `POST …/approve` |
| Executes code on hosts? | No | Only after deploy auth | Via Studio worker when up |

## Index and template

- [Capabilities and feature index](index.md) — what is live, plus FEAT-001…016
- [Mini-first dependency plan](PLAN-mini-first.md)
- [Feature specification template](TEMPLATE.md)
- Core specs: [FEAT-010 harness](FEAT-010-mini-personal-agent-loop.md), [FEAT-011 providers](FEAT-011-frontier-model-access.md)
- Protocol: [Work Order Protocol adoption](../work-order-protocol/README.md), [`AGENT_PROCESS.md`](../../AGENT_PROCESS.md)
- GitHub issues: [#2](https://github.com/sgerhart/ai-lab/issues/2)–[#12](https://github.com/sgerhart/ai-lab/issues/12)

## Honesty

Scaffolded ≠ implemented ≠ deployed ≠ live-verified. See [../roadmap.md](../roadmap.md).
