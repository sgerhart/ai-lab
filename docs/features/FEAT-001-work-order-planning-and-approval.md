# FEAT-001 — Feature backlog and work-order planning

- **Status:** Specified
- **Created:** 2026-09-21
- **Priority:** 1
- **Owner:** human (operator)
- **GitHub issue:** [#2](https://github.com/sgerhart/ai-lab/issues/2)

## Purpose

Turn lab ideas into **reviewed feature specifications** and **bounded implementation work orders** before any code or host change runs. A future planning agent may help draft; a human always approves the plan. This feature does **not** create runtime work orders on the M1 and must not execute or self-approve.

## User workflow

1. Human (or IDE) states an objective in natural language (for example “add a retry UI”).
2. Planning agent reads **only authorized repository context** (this repo’s docs, ADRs, policies, and declared paths). It does not scrape secrets, overlays, or adjacent product trees unless an ADR explicitly allows a path.
3. If the objective is ambiguous, the agent **asks clarifying questions** and stops until answered.
4. Agent drafts or updates a feature specification under `docs/features/` (from [TEMPLATE.md](TEMPLATE.md)).
5. Agent proposes one or more **implementation work orders** with dependencies, acceptance criteria, tests, and out-of-scope.
6. Human **approves**, edits, or rejects the plan (Git review and/or GitHub issue). No automatic merge.
7. Only after approval may engineers (human or later coding agent under FEAT-007) implement. Deploy still needs a **separate** authorization.
8. Runtime execution on `mac-mini` (FEAT-002+) is a different workflow and is not started by planning alone.

## Target host(s)

| Role | Host alias | Why |
|------|------------|-----|
| Authoring / review | `mac-air` | IDE, Git, GitHub |
| Spec store | Git (`sgerhart/ai-lab`) | Source of truth (ADR 0001) |
| Runtime (not this feature) | `mac-mini` | Only after a separate submit |

## Dependencies

- ADRs: 0001 (Git SoT), 0006 (phase-gated deploy), 0018 (human approval), 0020 (LangGraph is for runtime workflows—not a substitute for this planning gate)
- Existing historical phase WOs for context only (`WO-000`–`WO-007`)
- Does **not** require Studio

## Proposed deliverables

- This features tree (`README`, `index`, `TEMPLATE`, FEAT specs)
- Optional planning-agent module later (read-only tools + question loop)
- Issue/PR checklist that blocks merge without human approval of the feature plan
- Explicit prohibition in agent policy: no `deploy`, no runtime `POST /v1/work-orders` from the planner, no self-approval

## Proposed implementation work orders

| ID (proposed) | Title | Depends on | Acceptance (sketch) |
|---------------|-------|------------|---------------------|
| IWO-001-a | Features docs + index + template (this change) | — | Validation finds `docs/features/`; lifecycle documented |
| IWO-001-b | Planning agent read-only context loader | IWO-001-a | Unit tests; refuses secret/overlay paths |
| IWO-001-c | Clarify-and-draft loop (no execute) | IWO-001-b | Produces FEAT/IWO Markdown; exits awaiting human |
| IWO-001-d | Policy: planner cannot approve or dispatch | IWO-001-b | Tests assert privileged tools denied |

## Acceptance criteria

- [x] Lifecycle Idea → … → verified completion documented
- [x] Feature vs implementation WO vs runtime WO distinguished
- [x] Nine owner-priority capabilities indexed with stable IDs
- [ ] Planning agent implemented (future IWOs)
- [ ] Planner cannot call deploy, model pull, or runtime submit
- [ ] Planner cannot mark its own plan approved
- [ ] Human approval recorded before implementation starts

## Out of scope

- Automatic execution of drafted IWOs
- Self-approval or silent merge
- Creating Postgres runtime work orders
- Deploy, `brew bundle --apply`, compose `up`, model pulls
- Rewriting Clarion / agentic-factory product orchestration
- Renaming historical `WO-000`–`WO-007` into FEAT IDs

## Implementation status (honest)

| Layer | Status | Evidence |
|-------|--------|----------|
| Spec in Git | Done (this file + index) | `docs/features/` |
| Code (planning agent) | Not started | — |
| Host deploy | n/a | Docs only |
| Live verified | n/a | — |

## Notes

Adjacent Air stacks (Clarion, agentic factory, IDEs) stay outside this feature (ADR 0007, 0025). The planner must not treat them as lab hosts or copy their secrets.
