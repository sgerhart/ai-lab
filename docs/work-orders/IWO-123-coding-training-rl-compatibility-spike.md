# IWO-123 — Coding Training RL Backend Compatibility Spike

**Status:** Complete (WO-07 Delivered)  
**Priority:** P2  
**Effort:** M  
**Owner:** Steven Gerhart  
**Feature:** FEAT-024  
**Services / Areas:** `coding-training/services/model/`, `coding-training/packages/contracts/`, `coding-training/tests/unit/`, docs

## Problem

Prior to implementing full-scale execution-reward reinforcement learning (WO-08), we must validate whether Apple Silicon unified memory workstations (`mac-studio`) can execute on-policy policy gradient updates efficiently. Standard PPO requires a separate value critic network, which roughly doubles weights memory footprint and requires two backward computational graphs per rollout. We must verify if Group Relative Policy Optimization (GRPO) eliminates the critic bottleneck, normalizes advantages cleanly across small group sizes ($G=4$), stabilizes policy ratios with clipped objectives and Schulman KL divergence penalties, and produces non-zero gradients with verifiable parameter divergence.

## Decision Context

- Implements RL compatibility spike per FEAT-024 roadmap and ADR 0001 (Apple Silicon unified memory MLX optimization).
- Implements `packages/contracts/rl.py`: typed Pydantic contracts for `RolloutCandidate`, `RolloutGroup`, `PolicyGradientStepResult`, and `RLSpikeReport`.
- Implements `services/model/rl_spike.py`:
  - `compute_grpo_advantages`: zero-mean group advantage normalization across $G=4$ rollouts without requiring a separate value critic network.
  - `compute_grpo_token_loss`: clipped surrogate objective with importance sampling ratio and Schulman KL divergence penalty.
  - `RLCompatibilitySpike`: executes on-policy policy gradient update, proving $\|\nabla_\theta \mathcal{L}\|_2 > 0$ and parameter divergence (`initial_param_hash != updated_param_hash`).
- Implements CLI runner `scripts/run_rl_spike.py` generating `reports/rl_spike_report.json`.
- Authors `docs/spikes/SPIKE-01-apple-silicon-rl-compatibility.md` with mathematical proofs, memory footprint analysis, and architectural recommendations for WO-08.
- Enforces strict safety defaults: `EXECUTION_ENABLED=false` and `TRAINING_ENABLED=false`.

## What To Build / Fix

1. Implement `packages/contracts/rl.py`: typed contracts for rollouts, groups, gradient steps, and spike findings.
2. Export RL contracts in `packages/contracts/__init__.py`.
3. Implement `services/model/rl_spike.py`: mathematical advantage normalization, token loss clipping, KL divergence, and on-policy gradient step engine.
4. Export `RLCompatibilitySpike`, `compute_grpo_advantages`, `compute_grpo_token_loss` in `services/model/__init__.py`.
5. Implement `scripts/run_rl_spike.py`: CLI spike runner generating reproducible report JSON.
6. Author `coding-training/docs/spikes/SPIKE-01-apple-silicon-rl-compatibility.md`.
7. Author gate record `coding-training/docs/gates/WO-07.md`.
8. Implement unit test suite `tests/unit/test_rl_spike.py` (5 tests covering advantage normalization, clipped surrogate loss, KL divergence penalty, parameter divergence, and report schema validation).
9. Update `docs/features/FEAT-024-execution-verified-coding-model-training.md` and `docs/features/index.md`.

## Expected Change Surface

- Expected: `coding-training/packages/contracts/rl.py`, `coding-training/services/model/rl_spike.py`, `coding-training/scripts/run_rl_spike.py`, `coding-training/reports/rl_spike_report.json`, `coding-training/docs/spikes/SPIKE-01-apple-silicon-rl-compatibility.md`, `coding-training/docs/gates/WO-07.md`, `coding-training/tests/unit/test_rl_spike.py`, `docs/work-orders/IWO-123-coding-training-rl-compatibility-spike.md`.
- Tests: `cd coding-training && make check`.
- Docs/status: `docs/features/index.md`, `docs/features/FEAT-024-execution-verified-coding-model-training.md`.

## Out Of Scope

- Full grouped rollout orchestrator connected to the controller execution loop (deferred to WO-08).
- Multi-host distributed sandbox execution (deferred to WO-09).
- Web console frontend (deferred to WO-10).

## Do NOT Change

- Do not modify existing AI Lab core services (`platform/`, `infrastructure/`).
- Do not commit adapter weights or checkpoints to Git.
- Do not run untrusted code directly on macOS host workstations.

## Closeout & Evidence

- Files created:
  - `coding-training/packages/contracts/rl.py`
  - `coding-training/services/model/rl_spike.py`
  - `coding-training/scripts/run_rl_spike.py`
  - `coding-training/reports/rl_spike_report.json`
  - `coding-training/docs/spikes/SPIKE-01-apple-silicon-rl-compatibility.md`
  - `coding-training/docs/gates/WO-07.md`
  - `coding-training/tests/unit/test_rl_spike.py`
- Verification commands executed:
  - `cd coding-training && make check` (61/61 tests pass, 0 ruff errors)
  - `python3 coding-training/scripts/run_rl_spike.py` (Step verified, finite loss, weight divergence verified)
  - `./scripts/validate-repo.sh` (Repository validation OK)
