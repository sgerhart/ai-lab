# IWO-116 — Coding Training Platform Reconnaissance and Scaffold

**Status:** Complete (WO-00 & WO-01 Delivered)  
**Priority:** P2  
**Effort:** M  
**Owner:** Steven Gerhart  
**Feature:** FEAT-024  
**Services / Areas:** `coding-training/`, docs, architecture, platform

## Problem

AI Lab needs an execution-verified model improvement platform to evaluate, fine-tune, and train local coding models against trusted unit tests without risking host compromise or data contamination. Before building services, the system requires architectural grounding, host topology inventory, security threat modeling, formal ADRs, and a clean local developer loop with typed contracts and test stubs.

## Decision Context

- Chosen approach: Sub-platform rooted at `coding-training/` following Specification v1.0.
- MLX on Mac Studio for model training (ADR 0001).
- Isolated Linux VM on Proxmox Security Compute for sandbox execution (ADR 0002).
- PostgreSQL lease scheduling for durable jobs; NATS deferred (ADR 0003).
- Content-addressed artifact storage (ADR 0004).
- Air-gapped network egress (`deny_all`) for execution jails (ADR 0005).

## What To Build / Fix

1. Complete WO-00 reconnaissance of AI Lab repository and deployment constraints.
2. Produce `coding-training/README.md` with safety invariants and roadmap.
3. Author `coding-training/docs/architecture.md` with topology and trust boundaries.
4. Author ADRs 0001–0005 under `coding-training/docs/adr/`.
5. Author gate verification documents `coding-training/docs/gates/WO-00.md` and `WO-01.md`.
6. Implement sub-platform scaffold: `pyproject.toml`, `Makefile`, typed schemas in `packages/contracts/`.
7. Implement `RewardEngine` with strict failure separation (infrastructure error != candidate failure).
8. Implement `MockModelBackend` and `MockSandboxBackend` for zero-privilege development.
9. Implement unit test suite (18 unit tests in `tests/unit/`).
10. Register FEAT-024 in `docs/features/`.

## Expected Change Surface

- Expected: `coding-training/`, `docs/features/FEAT-024-execution-verified-coding-model-training.md`, `docs/work-orders/IWO-116-coding-training-reconnaissance-and-scaffold.md`.
- Tests: `cd coding-training && make check`, `./scripts/validate-repo.sh`, `./scripts/preflight.sh`.
- Docs/status: `docs/features/index.md`.

## Out Of Scope

- Live provisioning of Proxmox VMs (requires separate operator action).
- Executing model code on Mac hosts.
- Downloading unreviewed datasets or weight files.

## Do NOT Change

- Do not modify existing AI Lab core services (`platform/`, `infrastructure/`).
- Do not run untrusted code on macOS.
- Do not change existing compose bindings or secrets.

## Closeout & Evidence

- Files created:
  - `coding-training/README.md`
  - `coding-training/pyproject.toml`
  - `coding-training/Makefile`
  - `coding-training/docs/architecture.md`
  - `coding-training/docs/adr/0001`–`0005`
  - `coding-training/docs/gates/WO-00.md` and `WO-01.md`
  - `coding-training/packages/contracts/` (configs, tasks, executions, rewards, models, checkpoints, attestation)
  - `coding-training/services/rewards/engine.py`
  - `coding-training/services/model/backend.py`
  - `coding-training/services/sandbox_worker/backend.py`
  - `coding-training/tests/unit/` (18 unit tests)
  - `docs/features/FEAT-024-execution-verified-coding-model-training.md`
- Validation:
  - `cd coding-training && make check`: 18 tests passed, ruff clean.
  - `./scripts/validate-repo.sh`: PASS (RESULT: OK).
  - `./scripts/preflight.sh`: PASS.
  - `python3 -m unittest discover -s tests -v`: 422 tests passed.
