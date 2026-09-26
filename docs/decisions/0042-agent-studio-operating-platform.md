# ADR 0042 — Agent Studio is an operating platform for personal work

- **Status:** Accepted (direction). The shell is in Git. It is not deployed by this ADR.
- **Date:** 2026-09-25
- **Related:** ADR 0018, 0020, 0037, 0038; FEAT-013, FEAT-017; D-019

## Context

Personal Agent Studio could chat, and it could save a thin agent record: a
title, a system prompt, a tool list, MCP ids, and a cron string. That is too
small for agents that build software, teach a topic, and help run a product
and a company.

The operator wants one studio that can grow: files, mail, and later a
portfolio, with room for other MCP servers when they are actually needed.
Enterprise consoles are not the first toolbelt.

## Decision

Treat Agent Studio as the design surface, the mini as the control plane, and
the existing runtime as the executor.

1. An agent record is model, instructions, context, memory, tools, skills,
   workflow, permissions, and runtime. Simple Mode hides everything except
   name, purpose, model, tools, knowledge, and run.
2. The page layout is three columns: the AI Lab menu, a collapsible Agent
   Studio menu, and a canvas. Chat remains the front door. Opening Agents
   opens the studio.
3. The first jobs are build, learn, product, and company. Mail and a
   read-only portfolio skill are add-ons. Transfers, send, push, and delete
   stay behind human approval (ADR 0018).
4. Extra builder fields live in a `studio` object on the agent definition.
   The agent kind and tool policy still decide what a run may call.
5. LangGraph stays the orchestrator (ADR 0020). A graph builder, agent-to-agent
   handoff, and remote runtimes are later work, not a new framework.
6. Local models stay the default (ADR 0038).

## Consequences

- IWO-063 replaces the old agent form with the studio shell.
- D-019 stays open until the operator accepts the live screen.
- A malware-analysis environment stays out of this repository.

## Alternatives considered

- Keep the single prompt form. Rejected. It cannot show tools, skills, memory,
  and permissions as separate parts.
- Build an enterprise integration catalog first. Rejected. The studio is for
  building, learning, and company work. Connections can be added when needed.
