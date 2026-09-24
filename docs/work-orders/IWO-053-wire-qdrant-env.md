# IWO-053 — Wire Qdrant into control-plane env (FEAT-008)

**Status:** Done  
**Priority:** P1  
**Effort:** S  
**Owner:** human (operator)  
**Feature:** [FEAT-008](../features/FEAT-008-research-retrieval-memory.md)  
**Risk tier:** P1  

## Problem

Qdrant is healthy on the mini, but `/v1/memory/status` reports
`backend=memory` because `~/.ai-lab/start-control-plane.sh` does not export
`QDRANT_API_KEY` / `QDRANT_URL`.

## Decision Context

- Source key from gitignored `infrastructure/compose.local.env` (already set).
- Do not put the key in the LaunchAgent plist or Git.
- `scripts/wire-qdrant-env.sh` dry-run / `--apply` updates start script +
  restarts `com.ai-lab.control-plane`.

## What To Build / Fix

- `scripts/wire-qdrant-env.sh`
- Apply on mini; verify `/v1/memory/status` → `backend=qdrant`
- Smoke upsert + search
- Docs: FEAT-008 live status, mini RUNBOOK note

## Out Of Scope

- New embedding model (hash_v1 stays)
- Changing Qdrant image / volumes
- Rotating the API key (use rotate runbook separately)

## Acceptance Criteria

1. Dry-run does not edit the start script.
2. After `--apply`, memory status uses Qdrant.
3. Upsert + search round-trip returns the stored source (no fabrication).

## AI Lab gates

- **Host deploy authorized?** Yes — operator Continue after Qdrant listed as
  mini/studio next step (2026-09-24). Restarts control plane only; no compose
  recreate.
- Secrets never printed or committed.

## Closeout

- Verification evidence: After `--apply` on mini, `/v1/memory/status` returned
  `backend=qdrant`, `ok=true`. Upsert + search round-trip returned source
  `iwo-053-smoke` with score ~0.63 (2026-09-24).
- Host deploy performed? Yes — updated `~/.ai-lab/start-control-plane.sh` and
  restarted `com.ai-lab.control-plane` (no compose recreate). Secrets not printed.
