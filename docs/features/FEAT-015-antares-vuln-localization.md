# FEAT-015 — Antares vulnerability-localization agent (Studio)

- **Status:** Idea / Specified
- **Created:** 2026-09-24
- **Owner:** human (operator)
- **GitHub issue:** draft only

## Purpose

Run Cisco Foundation AI **Antares** models as a **dedicated** sandboxed
terminal agent for vulnerability *file localization* — not general Studio chat.
Prefer **Antares-1B** on `mac-studio`; optional **Antares-350M** as a lighter
or draft model. Findings require human review; no autonomous remediation.

## User workflow

1. Operator authorizes a model pull / weight placement on Studio (never Git).
2. Lab exposes an OpenAI-compatible or Ollama endpoint for the Antares weights.
3. Antares CLI (or a lab wrapper) runs against a **read-only repo snapshot** in a
   network-disabled sandbox.
4. Output (paths / SARIF / JSON) lands as a Studio artifact or memory upsert with
   explicit `source`; operator reviews before any fix work (FEAT-007 optional).

## Target host(s)

| Role | Host alias | Why |
|------|------------|-----|
| Inference + sandbox | `mac-studio` | 64 GB compute; keep mini as SoT |
| Orchestration / UI | `mac-mini` | Optional job submit later |
| Review | `mac-air` | Human + DefenseClaw |

## Dependencies

- FEAT-003 (Studio models), FEAT-010 (agent loop), FEAT-008 (optional memory)
- FEAT-014 recommended when tooling is hooked
- Model cards: [antares-1b](https://huggingface.co/fdtn-ai/antares-1b),
  [antares-350m](https://huggingface.co/fdtn-ai/antares-350m)

## Proposed deliverables

- Feature + ADR if sandbox policy needs expansion
- Runbook: pull, sandbox, CLI, review
- Optional agent definition `vuln-localize` (no write tools)

## Proposed implementation work orders

| ID | Title | Depends on | Acceptance |
|----|-------|------------|------------|
| IWO-047 | Antares-1B on Studio (pull gated) | FEAT-003 | Model serves; no Git weights |
| IWO-048 | Network-disabled sandbox runner | IWO-047 | Repo snapshot; timeout; destroy after run |
| IWO-049 | Studio UI / definition hook | IWO-048 | Operator can launch + retrieve SARIF |

## Acceptance criteria

- [ ] Prefer 1B documented; 350M optional
- [ ] Sandbox `network=none` (or equivalent) before any live run
- [ ] No auto-remediation tools
- [ ] Weights never in Git

## Out of scope

- General-purpose chat with Antares
- Exploit generation
- Pulling models without explicit authorization

## Implementation status

| Layer | Status |
|-------|--------|
| Spec | Done (this file) |
| Code | Not started |
| Live | No |
