# IWO-063 — Agent Studio shell

**Status:** In progress (code in the working tree; live operator pass not recorded)  
**Priority:** P2  
**Effort:** M  
**Feature:** [FEAT-017](../features/FEAT-017-agent-operating-studio.md)  
**Services / Areas:** platform

## Problem

The Agents page is a short form: name, three kinds, a prompt, and optional cron.
It does not match the studio the operator asked for: a collapsible menu beside
the AI Lab panel, and a canvas for designing agents that build, teach, and help
run a company.

## Decision Context

- Chosen approach: a second column and a canvas inside the existing Studio page, saving extra fields on the agent definition.
- Alternatives rejected: a separate app, or an enterprise MCP catalog as the first screen.
- Assumptions: chat remains the default view. The agent kind still gates tools.
- Open decisions: D-019 until the operator accepts the live layout.

## What To Build / Fix

- `studio-rail` to the right of the AI Lab sidebar, with the same collapse behavior.
- Canvas sections: Dashboard, My Agents, Templates, Published, Skills, Tools, Knowledge, Memory, Workflows, Runs, Evaluations, Permissions.
- Simple Mode: Name, Purpose, Model, Tools, Knowledge, Instructions, Run.
- Advanced Mode: identity, instructions, model, context, memory, tools, skills, knowledge, workflow, permissions, runtime, versions.
- `studio` object on `POST` and `PUT /v1/agent-definitions`.

## Expected Change Surface

- Expected: `agents.html`, `web/static/studio.css`, `web/static/studio.js`, `agent_definitions.py`, `control_app.py`
- Tests: definition round-trip; page contains the rail and canvas
- Docs/status: ADR 0042, FEAT-017, architecture page

## Out Of Scope

- Mail connect, portfolio transfers, eval execution, multi-agent graphs
- Host deploy

## Do NOT Change

- Chat as the default surface
- Approval before patch or commit
- Deny-by-default MCP
- Local model default

## Acceptance

- [x] Agent Studio menu collapses and the canvas remains
- [x] A definition saves purpose, tools, and memory policy in `studio`
- [x] Run still queues through the existing definition run API
- [ ] Operator uses the live page and accepts or rejects the layout
