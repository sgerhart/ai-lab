# FEAT-003 — Studio inference and worker integration

- **Status:** Specified (partial code)
- **Created:** 2026-09-21
- **Owner:** human (operator)
- **GitHub issue:** [#4](https://github.com/sgerhart/ai-lab/issues/4)

## Purpose

Serve local models on the Studio and optionally run isolated workers for heavy
or sandboxed steps. The mini remains the agent-lifecycle owner (ADR 0037);
Studio provides **inference bytes** and compute—not the work-order database.

## User workflow

1. Owner authorizes Studio host bring-up (Tailscale, Brewfile, Ollama).
2. Mini model router (FEAT-011) targets Studio Ollama/MLX.
3. Agent loop on mini calls Studio; artifacts/status return to mini.
4. Optional: dedicated Studio worker for privileged/isolated tool execution.

## Target host(s)

| Role | Host alias | Why |
|------|------------|-----|
| Inference / workers | `mac-studio` | 64 GB compute plane |
| Router / SoT | `mac-mini` | Policy + durability |
| Operator | `mac-air` | Authorize deploy |

## Dependencies

- FEAT-010, FEAT-011; ADR 0010, 0019, 0037
- Host: Studio on tailnet (not yet)

## Proposed deliverables

- Studio `--apply` + Ollama/MLX runbooks (host auth)
- Worker service when needed beyond HTTP Ollama
- Catalog entries; **no silent pulls**

## Proposed implementation work orders

| ID | Title | Depends on | Acceptance |
|----|-------|------------|------------|
| IWO-003-host | Studio Tailscale + setup (deploy gate) | Owner auth | `mac-studio` reachable |
| IWO-004-c | Ollama provider against Studio | IWO-004, host | Health + completion |
| IWO-003-worker | Optional isolated worker | host | Plan step on Studio |

## Acceptance criteria

- [ ] Studio on tailnet; Ollama health from mini
- [ ] Agent run completes with Studio model (or fails visibly)
- [ ] No silent `ollama pull`

## Out of scope

- Moving Postgres SoT to Studio; Air as inference plane; Clarion factory

## Implementation status (honest)

| Layer | Status | Evidence |
|-------|--------|----------|
| Spec | Done | this file |
| Code | Partial | worker + ollama client unit-tested |
| Deploy | No | Studio not on tailnet |
| Live verified | No | — |

## Notes

Distinct from FEAT-010 (loop on mini) and FEAT-006 (Jupyter).
