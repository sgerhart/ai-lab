# FEAT-016 — Local coding models and Coding Assistant

- **Status:** Partial (profiles, role overlay, read tools, isolated patch/commit, and one live bench are in place. The bench did not drop the coding profile. PR delivery is not started. Studio agent screen UX is open — D-019)
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
3. **Writes stay gated.** Reads need no approval. `apply_patch` and `git_commit`
   run only in a harness worktree after approval of that exact action. Push, PR,
   tests, and unattended writes are still out.
4. **Model IDs are configuration.** Catalog + profiles; verify tags on Studio before
   claiming pull defaults.
5. **Permissions are explicit.** Agent cannot invent workspace scope or privileged tools.
6. **Clarion stays out.** No Clarion repo as first test target; Air IDE use stays ordinary IDE use.

## Initial model profiles (config; not hard-coded business logic)

| Profile id | Intended use | Catalog / pulll candidate (verify on Studio before pull) |
|------------|--------------|----------------------------------------------------------|
| `qwen36-local` | Default chat. Coding quality is not measured yet | Ollama library tag `qwen3.6:35b-a3b` (Q4_K_M) |
| `general-local` | General agents, architecture, reasoning | Ollama library tag `qwen3.8:27b` (Apple Silicon may prefer `qwen3.8:27b-mlx`) |
| `coding-local` | Repo analysis, implementation, tests, diff review | Ollama library tag `qwen3-coder:30b` (~19 GB Q4_K_M) |
| `fast-local` | Smoke / regression | Existing Studio smoke model `llama3.2:3b` |
| `frontier-coding` | Explicit hard coding tasks | Existing gated OpenAI/Anthropic adapters (IWO-021) |

**Git does not record a pull.** On 2026-09-25 the Studio list included
`qwen3.6:35b-a3b` (Q4_K_M), `qwen3.8:27b`, `qwen3-coder:30b`, and `llama3.2:3b`.
The owner asked to make `qwen36-local` the chat default. Catalog `status` stays
`catalogued-not-pulled` and `pull_authorized` stays false.
The Models page can assign those installed tags to General, Coding, and Fast.
That overlay is `~/.ai-lab/model-roles.json` on the mini. Until Save, chat
still opens on `qwen36-local`. After Save, chat opens on General.
The 2026-09-25 bench scored all three large tags 4/4 on the short fixture.
That did not show the coder winning, so Coding Local stays `qwen3-coder:30b`.
Installed is not the same as resident: Ollama loads a tag on demand and keeps
it for a short idle window, so two large models can sit in memory together.

## User workflow (current code)

Chat is a conversation. An agent is a standing definition you can run again.

1. In Studio, pick a model from tags Ollama actually has. The menu leads with the tag. On Models, assign General, Coding, and Fast, then Save, if you want chat to open on General. Unavailable local models do not fall through to a paid API.
2. Create an agent and choose Coding, Lab check, or Research. Schedule and extra connections are optional. The screen layout is provisional (D-019).
3. For Coding, prepare a separate git copy. A run without one can read the control-plane checkout and cannot patch it.
4. Describe the task. Read tools run inside that workspace. A patch or commit waits for approval of that exact action, and both refuse the primary checkout.
5. Push, pull requests, and test runs are still denied.

## Implementation work orders

| ID | Title | Status |
|----|-------|--------|
| [IWO-055](../work-orders/IWO-055-coding-model-profiles-routing.md) | Model profiles + Studio routing + UI | Complete (unit; Git does not mark models pulled) |
| [IWO-056](../work-orders/IWO-056-readonly-coding-assistant.md) | Read-only Coding Assistant + fixture workspace | Complete (unit) |
| [IWO-057](../work-orders/IWO-057-model-bench.md) | Studio model comparison on short fixtures | Complete (unit + one live pass; fixture did not drop the coding profile) |
| [IWO-058](../work-orders/IWO-058-isolated-coding-worktree.md) | Isolated worktree, patch, commit, exact approval | Complete (unit). Tests and PR tools were left out |

### Hardening still thin after IWO-058

| Prerequisite | Status (2026-09-24) |
|--------------|---------------------|
| Fail-closed API auth | Live (session + token + trusted_tailnet) |
| Safe secrets handling | Live file store; Vault scaffold only |
| Durable run + restart recovery | Partial (unit + Postgres path when `DATABASE_URL` is set) |
| Action-specific approvals | Unit-complete; Studio shows the approval |
| Side-effect / retry safety | Partial |
| Execution budgets | Thin |
| Workspace isolation | Worktree marker + path check for patch/commit. Push still denied |

## Acceptance criteria (Feature-level)

- [x] Operator can choose a Coding agent definition
- [x] Operator can select installed local models from Studio tags
- [x] Inference routes mini → Studio Ollama
- [x] Unavailable local model → honest error; no paid fallback
- [x] Read tools stay inside the workspace; `../` is denied (unit)
- [x] Patch and commit require approval and an isolated worktree (unit)
- [ ] Operator has finished a live coding run and approved a patch
- [x] IWO-057 compared the default, the coder, and the general tag on a short fixture (2026-09-25). It did not separate them
- [ ] Docs and the Studio screen agree after the UX decision (D-019)
- [x] Clarion is not the first target

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
| Code | Partial | Profiles, `/v1/models` choices, read tools, worktree patch/commit |
| Deploy / live | Partial | Mini routes to Studio Ollama. Four local tags were installed 2026-09-25, including `qwen3.6:35b-a3b`. Git does not mark them pulled. Role Save has not been recorded. No live approved patch recorded |
| Pulls | Operator-authorized on Studio, not by Git | Further pulls still need a separate yes |
| UX | Open | D-019 — do not treat the current New agent form as final |
