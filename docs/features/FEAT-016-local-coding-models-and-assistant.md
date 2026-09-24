# FEAT-016 — Local coding models and Coding Assistant

- **Status:** Partial (IWO-055 complete — profiles + Studio model picker; no qwen pulls yet)
- **Created:** 2026-09-24
- **Owner:** human (operator)
- **Priority:** Optional workload on FEAT-010 / FEAT-011 (not a separate product)
- **Related:** [FEAT-007](FEAT-007-coding-agent-pr-workflow.md) (later PR delivery), [FEAT-011](FEAT-011-frontier-model-access.md), [FEAT-003](FEAT-003-studio-worker-and-models.md), ADR 0007 / 0018 / 0038

## Purpose

Give the operator a **local coding capability inside AI Lab**: selectable coding-capable
Studio Ollama models, a reusable **Coding Assistant** agent definition, and bounded
repository tools—without creating a second agent framework or absorbing Clarion
(ADR 0007).

Mini harness routes inference to Studio. Mini must not load 27B/30B-class models
locally.

**Studio model selection (IWO-055):** The Agents UI lists models returned by Studio
Ollama `/api/tags`. Multiple models may be installed at once; Ollama typically
loads weights on demand when a model is selected (not all resident simultaneously).

## Product principles

1. **Studio-first local inference.** Coding profiles route to Studio Ollama.
2. **No silent paid fallback** (ADR 0038). Unavailable local model → clear error / blocked.
3. **Read-only first.** File edit / worktree / unattended write require hardening
   prerequisites (see IWO-D gate below).
4. **Model IDs are configuration.** Catalog + profiles; verify tags on Studio before
   claiming pull defaults.
5. **Permissions are explicit.** Agent cannot invent workspace scope or privileged tools.
6. **Clarion stays out.** No Clarion repo as first test target; Air IDE use stays ordinary IDE use.

## Initial model profiles (config; not hard-coded business logic)

| Profile id | Intended use | Catalog / pulll candidate (verify on Studio before pull) |
|------------|--------------|----------------------------------------------------------|
| `general-local` | General agents, architecture, reasoning | Ollama library tag `qwen3.8:27b` (Apple Silicon may prefer `qwen3.8:27b-mlx`) |
| `coding-local` | Repo analysis, implementation, tests, diff review | Ollama library tag `qwen3-coder:30b` (~19 GB Q4_K_M) |
| `fast-local` | Smoke / regression | Existing Studio smoke model `llama3.2:3b` |
| `frontier-coding` | Explicit hard coding tasks | Existing gated OpenAI/Anthropic adapters (IWO-021) |

**Not pulled by Git or IWOs.** Owner must authorize each `ollama pull` separately.
Do not assume coding-local beats general-local—IWO-C evaluates both.

## User workflow (target)

1. Select Coding Assistant in Studio Agents UI.
2. Choose model profile (see actual model id + billing class).
3. Select authorized repository / workspace (fixture first—not Clarion).
4. Enter objective or Work Order reference.
5. See read-only vs write-enabled mode.
6. Run → inspect tool steps → plan / evidence.
7. Later (IWO-D): worktree, tests, diff, exact-action approval for delivery.

## Proposed implementation work orders

| ID | Title | Gate |
|----|-------|------|
| [IWO-055](../work-orders/IWO-055-coding-model-profiles-routing.md) | Model profiles + Studio routing + UI/audit | No pulls / no host mutate |
| IWO-056 | Read-only Coding Assistant + repo tools + fixture workspace | Depends on IWO-055 |
| IWO-057 | Coding-model evaluation (fixture tasks) | Depends on IWO-055; optional IWO-056 |
| IWO-058 | Isolated write workflow (worktree, patch, tests, exact approvals) | **Blocked** until hardening checklist passes |

### Hardening checklist before IWO-058 (write)

| Prerequisite | Current honest status (2026-09-24) |
|--------------|-------------------------------------|
| Fail-closed API auth | Live (session + token + trusted_tailnet) |
| Safe secrets handling | Live file store; Vault scaffold only |
| Green CI / validate-repo | Expected on PRs; confirm before IWO-058 |
| Independent mini-side worker | Partial (IWO-031; live when DATABASE_URL) |
| Durable run + restart recovery | Partial (unit + Postgres path) |
| Action-specific approvals | Unit-complete (IWO-007); UI partial |
| Side-effect / retry safety | Partial |
| Execution budgets | Thin / incomplete |
| Workspace isolation + tool restrictions | `bounded_scope` path check; write tools mostly policy-only stubs |

## Acceptance criteria (Feature-level — first release = IWO-055+056)

- [ ] Operator can choose Coding Assistant
- [ ] Operator can select verified coding/general local models (when installed)
- [ ] Inference routes mini → Studio Ollama
- [ ] Run records provider + model actually used
- [ ] Read-only inspect of authorized **fixture** repo; unauthorized paths denied
- [ ] Unavailable model → honest error; no paid fallback
- [ ] Docs state what is implemented vs live-verified
- [ ] Clarion not used as first target

## Out of scope

- Separate coding-agent product or framework (CrewAI, AutoGen, etc.)
- Moving Clarion into this repo
- Automatic model downloads
- Self-merge / silent push / deploy
- Replacing Cursor/IDE local coding on Air

## Implementation status (honest)

| Layer | Status | Evidence |
|-------|--------|----------|
| Spec | Done | this file |
| Code | Partial | IWO-055 catalog profiles + `/v1/models` choices + Studio picker |
| Deploy / live | Partial | Uses live Ollama tags when mini→Studio configured; qwen not pulled by this Feature |
| Pulls | Not authorized | Owner must authorize `ollama pull` separately |
