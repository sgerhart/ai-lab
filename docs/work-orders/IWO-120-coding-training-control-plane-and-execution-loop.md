# IWO-120 — Coding Training Control Plane and Execution Loop

**Status:** Complete (WO-04 Delivered)  
**Priority:** P2  
**Effort:** M  
**Owner:** Steven Gerhart  
**Feature:** FEAT-024  
**Services / Areas:** `coding-training/services/controller/`, `coding-training/tests/unit/`, docs

## Problem

The execution-verified coding model training platform requires a durable, resilient control plane to coordinate tasks, model generations, sandboxed executions, and deterministic reward scoring. Without an atomic, crash-resilient queue with lease renewals and expiration recovery, jobs could be double-executed or permanently orphaned. Furthermore, the cardinal invariant must be strictly enforced: infrastructure failures must be marked unscorable (`reward=None`, audit action `investigate`), never conflated with candidate code failure (`0.0`).

## Decision Context

- Implements control plane and execution loop based on ADR 0003 (durable job state and lease lifecycle).
- Provides durable `JobStore` supporting SQLite (in-memory or file-backed) and PostgreSQL schemas with atomic lease claims (`claim_next_job`), renewals (`renew_lease`), and expiration recovery.
- Relational entities managed: `execution_jobs`, `candidates`, `executions`, `rewards`, and `audit_events`.
- Orchestrates pipeline via `ExecutionLoopOrchestrator`:
  1. Retrieve task definition and immutable test bundle reference.
  2. Query `ModelBackend` to generate candidate implementation.
  3. Hash candidate (`candidate_sha256`) and persist to store.
  4. Dispatch to `SandboxBackend` with safe timeout and policy.
  5. Compute deterministic reward via `RewardEngine`.
  6. Record immutable `AuditEvent` with actor, action, and decision.
  7. Transition job to terminal state `COMPLETED` or `FAILED`.
- Enforces cardinal invariant: sandbox infrastructure errors are unscorable, `reward=None`, audit decision `investigate`, NEVER scored `0.0`.
- Exposes FastAPI control plane daemon with REST API and SSE stream (`/v1/events/stream`) for the web console (WO-10).

## What To Build / Fix

1. Implement `services/controller/store.py`: Durable `JobStore` with atomic lease scheduling, heartbeat renewal, expired lease reclamation, and metrics calculation.
2. Implement `services/controller/loop.py`: `ExecutionLoopOrchestrator` tying together model inference, candidate hashing, sandboxed execution, reward calculation, and audit trails.
3. Implement `services/controller/app.py`: FastAPI daemon exposing `/v1/health`, `/v1/metrics`, `/v1/jobs`, `/v1/jobs/{job_id}`, `/v1/jobs/submit`, `/v1/audit/events`, and `/v1/events/stream`.
4. Export `AuditEvent` in `packages/contracts/__init__.py`.
5. Implement unit test suite `tests/unit/test_controller.py` (4 comprehensive tests covering lease lifecycles, orchestrator pipeline, unscorable infra failures, and API endpoints).
6. Document Gate WO-04 closeout record in `coding-training/docs/gates/WO-04.md`.

## Expected Change Surface

- Expected: `coding-training/services/controller/`, `coding-training/packages/contracts/__init__.py`, `coding-training/tests/unit/test_controller.py`, `coding-training/docs/gates/WO-04.md`, `docs/work-orders/IWO-120-coding-training-control-plane-and-execution-loop.md`.
- Tests: `cd coding-training && make check`.
- Docs/status: `docs/features/index.md`, `docs/features/FEAT-024-execution-verified-coding-model-training.md`.

## Out Of Scope

- Direct execution of untrusted code on macOS workstations (`mac-air`, `mac-mini`, `mac-studio`).
- Production PostgreSQL server provisioning on `mac-mini` (deferred to operator host action).
- Real model weights or MLX training loops (deferred to WO-05 and WO-06).

## Do NOT Change

- Do not modify existing AI Lab core services (`platform/`, `infrastructure/`).
- Do not assign `0.0` score to infrastructure failures.
- Do not bypass atomic leasing.

## Closeout & Evidence

- Files created:
  - `coding-training/services/controller/store.py`
  - `coding-training/services/controller/loop.py`
  - `coding-training/services/controller/app.py`
  - `coding-training/services/controller/__init__.py`
  - `coding-training/tests/unit/test_controller.py`
  - `coding-training/docs/gates/WO-04.md`
- Verification commands run:
  - `cd coding-training && make check` (41 passing unit tests, 0 lint errors in 1.729s)
  - All 4 test cases in `test_controller.py` pass 100%
