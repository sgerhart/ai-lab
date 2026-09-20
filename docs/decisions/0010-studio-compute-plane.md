# ADR 0010 — Studio is the compute plane

- **Status:** Accepted
- **Date:** 2026-09-20
- **Supersedes:** open decision D-004 (dedicated inference host)

## Context

Confirmed hardware: Mac Studio, Apple M5 Max, 18 CPU / 40 GPU cores, 64 GB unified memory, 1 TB internal SSD. This is the only machine sized for local LLM/SLM work.

## Decision

The Studio runs inference (Ollama initially), MLX / MLX-LM, PyTorch experiments, Hugging Face tooling, LoRA/SLM work, embeddings/rerank, JupyterLab, agent workers, and isolated coding-agent execution.

The Studio is **not** the home of durable agent state. 64 GB is shared with macOS and apps; do not assume it is all available to one model or to Docker.

Model downloads are explicit operations, never part of bootstrap. Model and dataset paths stay configurable for a future Thunderbolt NVMe volume. Until then, use the internal 1 TB SSD.

M5 Max software compatibility was **not validated in this workspace** (this workspace is an M3). First Studio boot must verify Ollama and MLX; record results in `hosts/studio/`.

## Consequences

- Workers on the Studio call control-plane APIs on the M1 over Tailscale.
- Bootstrap must not `ollama pull`.

## Alternatives considered

- Laptop-only inference — rejected;  the Air is the human plane and sleeps.
- NVIDIA/vLLM box — not present; vLLM is not the initial runtime (ADR 0019).
