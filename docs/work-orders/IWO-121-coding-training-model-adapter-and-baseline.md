# IWO-121 — Coding Training Model Adapter and Reproducible Holdout Baseline

**Status:** Complete (WO-05 Delivered)  
**Priority:** P2  
**Effort:** M  
**Owner:** Steven Gerhart  
**Feature:** FEAT-024  
**Services / Areas:** `coding-training/services/model/`, `coding-training/packages/evaluation/`, `coding-training/tests/unit/`, docs

## Problem

Accurate, reproducible evaluation of coding models requires standard prompt construction without leaking hidden test vectors, structured code extraction from diverse markdown outputs, and baseline holdout evaluation across strictly disjoint task families. Furthermore, the platform requires unified model backend abstractions (`ModelBackend`) supporting local Apple Silicon MLX inference, mock dry-runs, and network-attached `ModelWorker` endpoints on Mac Studio.

## Decision Context

- Implements model backend and evaluation based on ADR 0001 (MLX Apple Silicon optimization) and ADR 0002 (air-gapped sandbox execution).
- Provides `ModelBackend` protocol and implementations:
  - `MockModelBackend`: deterministic candidate generation for CI, test fixtures, and ground-truth verification.
  - `MLXModelBackend`: native Apple Silicon MLX and `mlx-lm` integration with PRNG seeding and dry-run fallback.
  - `HttpModelBackend`: zero-dependency HTTP client for Mac Mini controller talking to `ModelWorker` on `mac-studio:8090`.
- Implements `services/model/app.py`: FastAPI daemon hosting model endpoints (`/v1/health`, `/v1/capabilities`, `/v1/models/load`, `/v1/generate`).
- Implements `BaselineEvaluator` in `packages/evaluation/baseline.py`:
  - Formats standard completion prompts with zero hidden test vector disclosure.
  - Short-circuits syntax errors at compile time (`SYNTAX_ERROR`, `reward=0.0`).
  - Evaluates tasks against `SandboxWorker` and scores deterministic rewards.
  - Aggregates split metrics (`pass@1`, `mean_reward`, `syntax_valid_rate`, error counts).
  - Exports reproducible JSON reports.
- Verifies ground-truth ceiling: reference solutions achieve 100.0% pass@1 (30/30) across validation and test splits.

## What To Build / Fix

1. Implement `packages/contracts/evaluation.py`: Typed contracts for `TaskEvaluationResult`, `SplitMetrics`, `BaselineReport`.
2. Update `packages/contracts/__init__.py`: Export new evaluation contracts.
3. Implement `services/model/backend.py`: `ModelBackend`, `MockModelBackend`, `MLXModelBackend`, `HttpModelBackend`, and `extract_python_code`.
4. Implement `services/model/app.py`: FastAPI model serving application for Mac Studio on port 8090.
5. Implement `packages/evaluation/baseline.py`: `BaselineEvaluator` and `format_task_prompt`.
6. Implement `scripts/evaluate_baseline.py`: CLI tool for running baseline evaluations and exporting reports.
7. Implement unit tests in `tests/unit/test_model_backend.py` and `tests/unit/test_baseline_evaluator.py` (10 tests).
8. Generate holdout baseline reports: `reports/baseline_holdout.json` and `reports/baseline_holdout_untrained_mock.json`.
9. Document Gate WO-05 closeout record in `coding-training/docs/gates/WO-05.md`.

## Expected Change Surface

- Expected: `coding-training/packages/contracts/evaluation.py`, `coding-training/services/model/`, `coding-training/packages/evaluation/`, `coding-training/scripts/evaluate_baseline.py`, `coding-training/reports/`, `coding-training/tests/unit/`, `coding-training/docs/gates/WO-05.md`, `docs/work-orders/IWO-121-coding-training-model-adapter-and-baseline.md`.
- Tests: `cd coding-training && make check`.
- Docs/status: `docs/features/index.md`, `docs/features/FEAT-024-execution-verified-coding-model-training.md`.

## Out Of Scope

- Supervised LoRA fine-tuning parameter updates (deferred to WO-06).
- Direct execution of untrusted code on macOS workstations (`mac-air`, `mac-mini`, `mac-studio`).
- Deploying live containers or modifying host network bindings without authorization.

## Do NOT Change

- Do not modify existing AI Lab core services (`platform/`, `infrastructure/`).
- Do not disclose hidden test assertions in prompts.
- Do not allow cross-split family leaks.

## Closeout & Evidence

- Files created:
  - `coding-training/packages/contracts/evaluation.py`
  - `coding-training/services/model/app.py`
  - `coding-training/packages/evaluation/baseline.py`
  - `coding-training/packages/evaluation/__init__.py`
  - `coding-training/scripts/evaluate_baseline.py`
  - `coding-training/tests/unit/test_model_backend.py`
  - `coding-training/tests/unit/test_baseline_evaluator.py`
  - `coding-training/reports/baseline_holdout.json`
  - `coding-training/reports/baseline_holdout_untrained_mock.json`
  - `coding-training/docs/gates/WO-05.md`
- Verification commands run:
  - `cd coding-training && make check` (51 passing unit tests in 3.059s, 0 lint errors)
  - `python3 scripts/evaluate_baseline.py --splits val,test --use-reference` (100% pass@1 verified)
