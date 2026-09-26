# FEAT-017 — Agent Operating Studio

- **Status:** In progress (shell in Git, IWO-063)
- **Created:** 2026-09-25
- **Owner:** human (operator)
- **Priority:** Core product surface

## Purpose

Give the operator a studio for designing agents that help build things, learn,
and run a product and a company. Chat stays the conversation. The studio is
the design surface: a second menu and a canvas.

## User workflow

1. Open AI Lab and use chat as usual.
2. Choose Agent Studio. A second menu appears to the right of the AI Lab menu.
3. Collapse either menu.
4. Start from Dashboard or a template: Build, Learn, Product, Company, or Lab.
5. In Simple Mode set name, purpose, model, tools, knowledge, and instructions, then save.
6. Open Advanced Mode for instructions, memory policy, skills, workflow, permissions, and versions.
7. Run a saved agent. A build agent still changes files only in a separate copy after approval.
8. Inspect the run in Runs.

## Target host(s)

| Role | Host | Why |
|------|------|-----|
| UI + definitions | `mac-mini` | Control plane |
| Default inference | `mac-studio` | Ollama |
| Browser | `mac-air` | Human plane |

## Dependencies

- FEAT-013, FEAT-010, FEAT-016
- ADR 0018, 0020, 0038, 0042

## Proposed implementation work orders

| ID | Title | Depends on | Acceptance (sketch) |
|----|-------|------------|---------------------|
| [IWO-063](../work-orders/IWO-063-agent-studio-shell.md) | Studio rail, canvas, definition `studio` payload | FEAT-013 | Menu, builder, save, run |
| Later | Mail connect | IWO-063 | Read mail; send waits for approval |
| Later | Portfolio skill | IWO-063 | Read balances; no unsupervised transfer |
| Later | Eval runner and version compare | IWO-063 | Rerun a suite after a prompt or model change |
| Later | Workflow graph | IWO-063 | Manager stays default; graph is explicit |

## Acceptance criteria

- [x] Studio menu sits between the AI Lab menu and the canvas and collapses
- [x] Simple and Advanced builder save a definition
- [x] Build, learn, product, and company templates exist
- [x] Skills, tools, memory, workflows, evaluations, and permissions are reachable
- [x] A build run still requires the isolated copy and approval for edits
- [ ] Operator accepts the live screen (D-019)

## Out of scope

- Deploying this slice
- Enabling paid APIs
- Autonomous mail send, push, or crypto transfer
- Enterprise IT consoles as the default toolbelt
- Replacing LangGraph

## Implementation status (honest)

| Layer | Status | Evidence |
|-------|--------|----------|
| Spec | Done | this file, ADR 0042, agent-studio.md |
| Code | Partial | IWO-063 shell |
| Deploy | Not authorized | — |
| Live verified | No | Operator pass open |
