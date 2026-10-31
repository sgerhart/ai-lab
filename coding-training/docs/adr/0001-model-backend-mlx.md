# ADR 0001 — Model Backend and Apple Silicon Optimization

- **Status:** Accepted (WO-00)
- **Date:** 2026-10-30
- **Context:** `ai-lab/coding-training/`
- **Related:** `docs/decisions/0010-studio-compute-plane.md`, `0019-ollama-initial-inference.md`

## Context

The coding-training platform requires:
1. Low-latency, structured token generation on local Apple Silicon hardware.
2. Differentiable forward/backward passes for LoRA/QLoRA parameter fine-tuning on unified memory.
3. Potential on-policy token logprob extraction for reinforcement learning algorithms.

The Mac Studio (M5 Max, 64 GB unified memory) is the designated compute plane host. Ollama currently runs on `:11434` for general inference, but Ollama does not support backward passes or LoRA adapter gradient updates.

## Decision

1. **Primary Training Backend: Apple MLX & MLX-LM**
   - Use Apple's native MLX framework and `mlx-lm` for local fine-tuning and LoRA adapter updates on the Mac Studio.
   - Run a dedicated `ModelWorker` Python daemon on `mac-studio` exposing typed generation, SFT training, and adapter checkpointing endpoints over the tailnet.

2. **Inference & Generation Engine:**
   - Generation for evaluation and rollouts uses MLX-LM directly (or the local Ollama daemon as an evaluation-only baseline comparator).
   - The model parser enforces strict Python function extraction. Markdown backticks, conversational preambles, and system explanations are stripped or rejected; raw code syntax errors are treated as legitimate candidate failures.

3. **Candidate Model Selection:**
   - Small base coder model: `Qwen/Qwen3-0.6B` (or equivalent verified Apache-2.0 / permissive coder model compatible with MLX-LM).
   - Target parameter scale is under 1.5B parameters for the pilot to guarantee fast iteration loops, low memory pressure (<8 GB during LoRA training), and rapid test turnaround.
   - Pinned revisions: exact Hugging Face / model commit hash and tokenizer revision must be recorded in every experiment manifest.

## Consequences

- No external GPU cloud or CUDA dependencies are introduced for the core workflow.
- Training requires an MLX virtual environment on the Mac Studio (`uv sync` under `models/mlx` or `coding-training/services/model`).
- High-concurrency batching is limited by Apple Silicon unified memory bandwidth; generation parallelism is bounded by configuration (`MAX_EXECUTION_PARALLELISM=1` to `4`).
