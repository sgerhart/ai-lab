# FEAT-018 — AI Security Platform

- **Status:** Partial (IWO-065–067 in Git, unit-tested, not deployed)
- **Created:** 2026-09-26
- **Owner:** human (operator)
- **Priority:** Core security capability

## Purpose

Make security a first-class AI Lab platform service governing agents, tools,
MCP, models, code-analysis services, approvals, findings, and audit.

## Outcomes

- one security policy/evidence model across AI Lab
- common events from agents, MCP, Antares, DefenseClaw, approvals, and Vise
- governed MCP/tool capabilities
- agent security posture visible in Agent Studio
- Security UI becomes the operator console rather than a tool-specific page
- no dependence on the MacBook Air as a gateway

## Scope

- `platform/security/` common service layer
- security-event schema
- resource identities
- policy evaluation hooks
- Security Center API/UI
- integration with existing approvals and observability
- DefenseClaw and Antares as providers/integrations, not the whole security plane

## Dependencies

- FEAT-010
- FEAT-013
- FEAT-014
- FEAT-015
- FEAT-017
- ADR 0043

## Implementation Work Orders

- IWO-065 — security platform foundation
- IWO-066 — common security event and evidence model
- IWO-067 — MCP registry and governed capabilities
- IWO-068 — Agent Studio security posture
- IWO-069 — Security Center expansion

## Acceptance criteria

- [x] Security services have stable APIs and schemas (unit; `docs/security/event-envelope.md`)
- [x] Existing tool approvals remain authoritative
- [x] Security events are correlated to agent/run/tool/job identity
- [x] DefenseClaw and Antares integrations are optional providers (descriptors only; no live calls)
- [ ] Air is not a required gateway
- [ ] No new public service exposure
