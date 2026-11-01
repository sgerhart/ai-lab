# IWO-124 — Coding Training Execution-Reward RL Training

**Status:** Complete (WO-08 Delivered)  
**Priority:** P2  
**Effort:** M  
**Owner:** Steven Gerhart  
**Feature:** FEAT-024  
**Services / Areas:** `coding-training/services/model/`, `coding-training/scripts/`, `coding-training/tests/unit/`, docs

## Problem

Following the positive findings of the Apple Silicon RL compatibility spike (WO-07 / SPIKE-01), we need an operational execution-reward reinforcement learning engine. The trainer must sample grouped candidate rollouts ($G=4$) for programming prompts mined strictly from `Split.TRAIN`, dispatch rollouts to the isolated sandbox worker, score execution rewards, compute normalized group advantages without a value critic network (GRPO), update policy adapter parameters, enforce parameter divergence, package tamper-evident checkpoints, and evaluate performance on held-out validation tasks.

## Decision Context

- Implements execution-reward RL training based on SPIKE-01, ADR 0001 (Apple Silicon unified memory MLX optimization), and ADR 0004 (deterministic rewards and sandbox isolation).
- Implements `GRPOTrainer` in `services/model/grpo_trainer.py`:
  - Enforces zero-mean group advantage normalization across $G=4$ rollouts.
  - Enforces unscorable candidate exclusion: rollouts failing due to infrastructure errors (`INFRA_ERROR` / `is_infra_error == True`) must not receive 0.0 reward and are excluded from group statistics.
  - Enforces weight divergence invariant: initial adapter parameter hash must not equal final adapter parameter hash.
  - Packages and verifies checkpoints under `~/.ai-lab/models/adapters/` with `CheckpointManifest`.
- Updates `services/model/app.py`: exposes `POST /v1/train/rl`.
- Implements CLI utility `scripts/train_rl.py` with holdout validation evaluation.

## What To Build / Fix

1. Implement `services/model/grpo_trainer.py`: `GRPOTrainer` and `RLTrainingResult`.
2. Export `GRPOTrainer` and `RLTrainingResult` in `services/model/__init__.py`.
3. Update `services/model/app.py` with `TrainRLRequest` and `POST /v1/train/rl` endpoint.
4. Implement `scripts/train_rl.py`: CLI for running GRPO training sessions and evaluating checkpoints on holdouts.
5. Author gate record `coding-training/docs/gates/WO-08.md`.
6. Implement unit test suite `tests/unit/test_grpo_trainer.py` (6 tests covering weight divergence, zero-step failure, tamper detection, unscorable exclusion, and API endpoints).
7. Update `docs/features/FEAT-024-execution-verified-coding-model-training.md` and `docs/features/index.md`.

## Expected Change Surface

- Expected: `coding-training/services/model/grpo_trainer.py`, `coding-training/services/model/app.py`, `coding-training/scripts/train_rl.py`, `coding-training/reports/rl_holdout_comparison.json`, `coding-training/docs/gates/WO-08.md`, `coding-training/tests/unit/test_grpo_trainer.py`, `docs/work-orders/IWO-124-coding-training-execution-reward-rl.md`.
- Tests: `cd coding-training && make check`.
- Docs/status: `docs/features/index.md`, `docs/features/FEAT-024-execution-verified-coding-model-training.md`.

## Out Of Scope

- Deploying models or modifying production network routes without explicit operator authorization.
- Running untrusted code on macOS workstations (`mac-mini`, `mac-studio`, `mac-air`).
- Multi-node distributed worker orchestration (WO-09 handover).

## Do NOT Change

- Do not modify existing AI Lab core services (`platform/`, `infrastructure/`).
- Do not commit adapter weights or checkpoints to Git.
- Do not allow training without weight divergence verification.

## Closeout & Evidence

- Files created:
  - `coding-training/services/model/grpo_trainer.py`
  - `coding-training/scripts/train_rl.py`
  - `coding-training/reports/rl_holdout_comparison.json`
  - `coding-training/docs/gates/WO-08.md`
  - `coding-training/tests/unit/test_grpo_trainer.py`
- Verification commands executed:
  - `cd coding-training && make check` (67/67 tests pass, 0 ruff errors)
  - `python3 coding-training/scripts/train_rl.py` (Checkpoint verified, 100% pass@1 on holdout validation)
  - `./scripts/validate-repo.sh` (Repository validation OK)
