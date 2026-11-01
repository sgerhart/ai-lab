# IWO-122 — Coding Training Verified SFT LoRA on Apple Silicon

**Status:** Complete (WO-06 Delivered)  
**Priority:** P2  
**Effort:** M  
**Owner:** Steven Gerhart  
**Feature:** FEAT-024  
**Services / Areas:** `coding-training/services/model/`, `coding-training/packages/datasets/`, `coding-training/tests/unit/`, docs

## Problem

Supervised fine-tuning of local coding models requires training data mined exclusively from execution-verified solutions without leaking tasks from validation or test holdouts. Furthermore, training runs must be cryptographically verified: adapter weights must demonstrably diverge from initial parameters (`initial_adapter_hash != final_adapter_hash`), and checkpoint artifacts (`adapter_config.json`, `adapters.safetensors`, `manifest.json`) must be tamper-evident and traceable to git commits and dataset hashes.

## Decision Context

- Implements SFT LoRA fine-tuning based on ADR 0001 (Apple Silicon MLX and MLX-LM native optimization) and ADR 0004 (deterministic rewards and verified dataset mining).
- Implements `SFTDatasetMiner` in `packages/datasets/sft_miner.py`:
  - Mines prompt/completion pairs exclusively from `Split.TRAIN` (75 curated tasks).
  - Enforces zero leakage into `Split.VAL` or `Split.TEST`.
  - Formats data into JSONL for MLX-LM instruction tuning.
- Implements `SFTTrainer` in `services/model/sft_trainer.py`:
  - Supports MLX-LM LoRA fine-tuning with unified memory footprint tracking.
  - Enforces weight divergence invariant: initial adapter parameter hash must not equal final adapter parameter hash. Runs with zero optimizer updates fail closed.
  - Packages and verifies checkpoints with `CheckpointManifest` complying with typed schema.
- Updates `services/model/app.py`: exposes `/v1/train/sft`, `/v1/checkpoints`, `/v1/checkpoints/{id}`.
- Implements CLI utility `scripts/train_sft.py` with holdout validation evaluation.

## What To Build / Fix

1. Implement `packages/datasets/sft_miner.py`: `SFTDatasetMiner` for mining passing training solutions with zero holdout leakage.
2. Export `SFTDatasetMiner` in `packages/datasets/__init__.py`.
3. Implement `services/model/sft_trainer.py`: `SFTTrainer` with parameter divergence checks and checkpoint verification.
4. Export `SFTTrainer`, `SFTTrainingResult` in `services/model/__init__.py`.
5. Update `services/model/app.py` with `/v1/train/sft`, `/v1/checkpoints`, `/v1/checkpoints/{id}` endpoints.
6. Implement `scripts/train_sft.py`: CLI for dataset mining, LoRA training, and holdout evaluation.
7. Configure `coding-training/.gitignore` to ignore checkpoints, mined datasets, and binary weights per `AGENTS.md`.
8. Implement unit test suite `tests/unit/test_sft_trainer.py` (5 tests covering split disjointness, weight divergence, fail-closed behavior, tamper detection, and API endpoints).
9. Document Gate WO-06 closeout record in `coding-training/docs/gates/WO-06.md`.

## Expected Change Surface

- Expected: `coding-training/packages/datasets/sft_miner.py`, `coding-training/services/model/sft_trainer.py`, `coding-training/services/model/app.py`, `coding-training/scripts/train_sft.py`, `coding-training/.gitignore`, `coding-training/tests/unit/test_sft_trainer.py`, `coding-training/docs/gates/WO-06.md`, `docs/work-orders/IWO-122-coding-training-verified-sft-lora.md`.
- Tests: `cd coding-training && make check`.
- Docs/status: `docs/features/index.md`, `docs/features/FEAT-024-execution-verified-coding-model-training.md`.

## Out Of Scope

- Reinforcement learning policy gradient rollouts (deferred to WO-07 and WO-08).
- Direct execution of untrusted code on macOS workstations (`mac-air`, `mac-mini`, `mac-studio`).
- Deploying live containers or modifying host network bindings without authorization.

## Do NOT Change

- Do not modify existing AI Lab core services (`platform/`, `infrastructure/`).
- Do not commit adapter weights or checkpoints to Git.
- Do not allow training without weight divergence verification.

## Closeout & Evidence

- Files created:
  - `coding-training/packages/datasets/sft_miner.py`
  - `coding-training/services/model/sft_trainer.py`
  - `coding-training/scripts/train_sft.py`
  - `coding-training/.gitignore`
  - `coding-training/tests/unit/test_sft_trainer.py`
  - `coding-training/docs/gates/WO-06.md`
- Verification commands run:
  - `cd coding-training && make check` (56 passing unit tests in 2.782s, 0 lint errors)
  - `python3 scripts/train_sft.py --mine --evaluate-holdout` (weight divergence verified: initial != final hash; 100% pass@1 on validation holdout)
