# Mini-first personal-agent platform — dependency plan

**Status:** Planning only (this document does not authorize deploy).  
**Related:** FEAT-010, FEAT-011, FEAT-002–009; ADR 0036–0038; IWO-001+

## Goal

Always-on personal agents and AI experimentation on the three-host lab.
Core purpose is **not** an autonomous coding factory (FEAT-007 is optional).

## Entity reminder

| Entity | Role |
|--------|------|
| `FEAT-*` | Desired capability |
| Implementation WO (`IWO-*`) | Bounded engineering in Git |
| Runtime WO (UUID) | Mini Postgres execution record |

Ordinary chat, inference, or notebook cells are **not** automatic IWOs.

## Slice order

### Planning PR (this change)

Canonical protocol adoption (IWO-001), feature amendments, FEAT-010/011,
ADRs 0037–0038, bounded IWOs. **No host mutate.**

### First mini development slice

| IWO | Delivers |
|-----|----------|
| IWO-002 | Conversation + agent-run contract, Postgres, FakeBackend tests |
| IWO-003 | Authenticated private UI: agent/model select, chat, run status |

**Independent of Studio.** Tests use FakeBackend only.

### Second mini slice

| IWO | Delivers |
|-----|----------|
| IWO-004 | Model router + billing classes; cloud disabled |
| IWO-005 | Bounded LangGraph model/tool loop (lab-ops read-only) |

Live provider connection requires **separate** owner authorization + credentials.

### Third mini slice

| IWO | Delivers |
|-----|----------|
| IWO-006 | Background execution polish, restart recovery, cancel/safe retry |
| IWO-007 | Action-level approval UX; run detail; visible failures |

### Parallel Studio slice (host auth required)

| Track | Features / IWOs |
|-------|-----------------|
| Jupyter first | FEAT-006 milestone 1: IWO-011…015 |
| Inference | FEAT-003 + FEAT-011 Ollama provider |

Notebook cells do **not** go through the mini harness.

### Later

FEAT-005 MCP/client, FEAT-008 memory, FEAT-009 scheduler, FEAT-007 coding agent.

## First end-to-end acceptance (mini)

From Air: private UI → read-only personal agent → ≥2 real model/tool steps →
close Air → retrieve completed result. Unapproved tool stops at gate.
Studio/provider down → recoverable or visible fail—not vanish.

## Jupyter acceptance (independent)

Air browser → Studio JupyterLab (tunnel) → cell runs on Studio (hardware check).

## Authorization gates (stop and ask)

- Merge of this PR (if required by owner process)
- Studio Tailscale / Brewfile / Jupyter install
- Enabling any usage-billed API provider or live paid calls
- Model pulls; new privileged tools; compose/network changes

## First small implementation IWO (after plan merges)

**[IWO-002](../work-orders/IWO-002-agent-run-conversation-contract.md)** —
Agent-run and conversation contract on the mini with FakeBackend tests.
No Studio, no cloud $, no host `--apply`.
