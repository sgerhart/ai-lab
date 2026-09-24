# IWO-055 — Coding model profiles and Studio routing

**Status:** Complete (code + unit; Studio pulls not authorized by this IWO)  
**Priority:** P1  
**Effort:** M  
**Owner:** human (operator)  
**Feature:** [FEAT-016](../features/FEAT-016-local-coding-models-and-assistant.md)  
**Services / Areas:** platform, models, docs, agents (UI selection only)

Canonical implementation Work Order (ADR 0036). **IWO A** — catalog profiles +
routing + UI/audit. **No model downloads. No host mutate.**

## Delivered (2026-09-24)

- `models/catalog.json` profiles: `general-local`, `coding-local`, `fast-local`,
  `frontier-coding` + qwen catalog entries (`catalogued-not-pulled`).
- `model_catalog.py`: resolve profiles against live Studio Ollama tags; studio
  `choices` list; `LocalModelUnavailable` (no paid fallback).
- `GET /v1/models` returns `providers`, `profiles`, `choices`, `default_profile`.
- Agents Studio model dropdown lists **installed** Studio models (annotated with
  profile labels when matched) and shows local vs usage-billed.
- Unit tests in `tests/test_model_lab.py`.

**Note:** Ollama may keep many models *installed* at once; loading into unified
memory is usually one (or few) at a time when you switch. Selection is from
`/api/tags`, not a claim that all stay resident in RAM.

## Problem

Studio chat and agent runs can select provider/model pairs today, but there is
no first-class **model profile** layer (`general-local`, `coding-local`,
`fast-local`, `frontier-coding`). The Git catalog only listed
`llama3.2:3b` / MLX smoke entries. Operators need to pick whichever LLM is
**actually installed on Studio**, with clear billing class and no silent paid
fallback.

## Decision Context

- **Chosen approach:** Extend `models/catalog.json` + `model_catalog.py` with a
  `profiles` map; resolve profile → backend + model id in the existing
  `ModelRouter` / Agents UI; surface availability from Studio Ollama `/api/tags`
  (or existing health path); record resolved backend+model on agent-run /
  conversation metadata. Keep ADR 0038: never silent local→paid fallback.
- **Alternatives rejected:** Second inference stack; hard-coded model strings in
  agent loop; pulling weights from CI/IWO; loading 27B/30B on the mini.
- **Assumptions:** Studio Ollama remains the local inference endpoint configured
  on the mini (`STUDIO_OLLAMA_URL` / existing Ollama backend). Tags
  `qwen3.8:27b` and `qwen3-coder:30b` exist in the public Ollama library as of
  planning (2026-09-24); **Studio installation is unverified** until owner
  authorizes pull + live check.
- **Open decisions:** Prefer `qwen3.8:27b` vs `qwen3.8:27b-mlx` on Apple Silicon
  Studio—document after live verify, do not silently swap in Git as “pulled.”

## What To Build / Fix

1. **Catalog**
   - Add `profiles` to `models/catalog.json` (ids above → `catalog_model_id` or
     `backend` + `pull_name` references).
   - Add catalog entries for qwen general + coding candidates with
     `status: catalogued-not-pulled`, `pull_authorized: false`, honest notes.
   - Keep Fast Local pointing at existing smoke model entry.
   - Frontier Coding profile points at existing usage-billed backends (disabled
     until authorized)—no new cloud adapter.

2. **Router / API**
   - Resolve `profile` → `(backend, model)` for completions and agent runs.
   - Availability check: local profile unavailable → `403`/`409`/`503` with clear
     body (model missing / Ollama down)—**no** cloud substitute.
   - Extend `/v1/models` (or add `/v1/model-profiles`) to list profiles with
     billing class, resolved model id, and `available: bool` when Ollama is
     reachable.
   - Ensure agent-run / conversation records store **resolved** `backend` +
     `model` (and profile id when used).

3. **UI (Agents Studio only — minimal)**
   - Model / profile selector shows profile label, actual model id, and
     local vs usage-billed.
   - Unavailable local profile shows honest disabled/error state.

4. **Docs**
   - FEAT-016 + this IWO; index row; runbook note: pull commands require separate
     owner auth (do not run pulls in this IWO).
   - Cross-link FEAT-007 (later write/PR path).

## Expected Change Surface

- **Expected:** `models/catalog.json`, `platform/src/ai_lab_platform/model_catalog.py`,
  `model_router.py` (and/or thin `model_profiles.py`), `control_app.py` providers
  endpoint, `web/agents.html` selector wiring, unit tests, FEAT-016 / index.
- **Tests:** Catalog load; profile resolve; unavailable local does not call cloud;
  FakeBackend path unchanged for CI.
- **Docs/status:** honest “catalogued-not-pulled” until live verify.

## Out Of Scope

- `ollama pull` on Studio or mini
- Coding Assistant agent definition / repo tools (→ IWO-056)
- Evaluation harness (→ IWO-057)
- Worktree / patch / write tools (→ IWO-058)
- Clarion, Air product repos, new orchestration frameworks
- Changing default chat model without UI opt-in
- Committing secrets, weights, or claiming models are live

## Do NOT Change

- ADR 0038 no silent paid fallback
- Mini must not host 27B/30B inference
- Clarion / sibling product trees (ADR 0007)
- Existing lab-operations / research flows unless profile selection is additive
- Host firewall, Tailscale ACLs, Brewfile apply

## Acceptance Criteria

1. Catalog lists four profiles with configurable model ids; qwen entries
   `catalogued-not-pulled` / `pull_authorized: false`.
2. API or `/v1/models` exposes profiles with billing class + resolved model id.
3. Selecting a local profile routes through existing Ollama backend config (Studio URL).
4. Unit test: unavailable/missing local model → error; cloud backend not invoked.
5. Unit test: FakeBackend / CI path still works with `fast-local` or explicit fake.
6. Agents UI shows profile label + model id + local vs usage-billed (when wired).
7. `./scripts/validate-repo.sh` and `python3 -m unittest discover -s tests -v` pass.
8. Docs state: **not** live-verified for qwen pulls until owner authorizes.

## Validation Plan

- **Automated:** unittest for catalog + profile resolve + no-fallback; validate-repo.
- **Manual (optional, no pull):** If Studio already has tags, operator may smoke
  `/v1/models` availability — not required to close this IWO.
- **Evidence:** test output; catalog diff; screenshot or note of UI labels.

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none
- **May run on Air?** Yes (docs/UI/tests only)
- **Usage-billed API?** No live calls; frontier profile remains gated
- **Model pull?** **Not authorized** by this IWO

## Follow-on (do not merge into this PR)

| IWO | Scope |
|-----|--------|
| IWO-056 | Coding Assistant definition, authorized fixture repo, read-only tools |
| IWO-057 | Fixture eval: general-local vs coding-local |
| IWO-058 | Isolated write + exact approvals (after hardening checklist) |

## Owner authorization needed later (not this IWO)

```text
# On mac-studio — ONLY after explicit owner yes:
ollama pull qwen3.8:27b
# or Apple Silicon optimized tag after verify:
# ollama pull qwen3.8:27b-mlx
ollama pull qwen3-coder:30b
ollama list   # confirm tags
# Peak memory / concurrency policy — separate note in hosts/studio/
```

## Notes

FEAT-007’s historical IWO-030/031 ids were reused for scheduler/worker work.
Do **not** revive those numbers for coding; use IWO-055+.
