# Features and future capabilities

**Status:** Documentation backlog. No feature here is authorized for implementation or deploy under this file alone.  
**Updated:** 2026-09-21

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

A **bounded engineering task** (design, code, tests, docs). Identified historically as `WO-000`…`WO-007` for phases 0–7, and later as `IWO-…` (or GitHub issues) when tied to a feature. Has dependencies, acceptance criteria, explicit out-of-scope, and required tests. Completing an implementation work order in Git is **not** host deploy.

Historical phase records `WO-000`–`WO-007` remain under [`../work-orders/`](../work-orders/README.md). Do not rename them or claim they are live PostgreSQL jobs.

### 3. Runtime work order

An **execution record** on the M1 control plane (`POST /v1/work-orders`). Durable state, attempts, approvals, artifacts. Managed by LangGraph + Postgres (ADR 0020). Operators submit these from the Air; they are not Markdown files in this tree.

| Concern | Feature | Implementation WO | Runtime WO |
|---------|---------|-------------------|------------|
| Home | `docs/features/` | `docs/work-orders/` (+ future IWO) | Postgres on `mac-mini` |
| ID | `FEAT-NNN` | `WO-NNN` / `IWO-…` | UUID |
| Approves | Human plan / PR / deploy auth | Human review of code | Human `POST …/approve` |
| Executes code on hosts? | No | Only after deploy auth | Via Studio worker when up |

## Index and template

- [Future capabilities index](index.md) — nine planned capabilities (owner priority order)
- [Feature specification template](TEMPLATE.md)
- First specification: [FEAT-001 Feature backlog and work-order planning](FEAT-001-work-order-planning-and-approval.md)
- GitHub issues: [#2](https://github.com/sgerhart/ai-lab/issues/2)–[#10](https://github.com/sgerhart/ai-lab/issues/10) (one per capability)

## Honesty

Scaffolded ≠ implemented ≠ deployed ≠ live-verified. See [../roadmap.md](../roadmap.md).
