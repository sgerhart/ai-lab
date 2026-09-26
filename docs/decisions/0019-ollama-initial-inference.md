# ADR 0019 — Ollama as initial local inference

- **Status:** Accepted
- **Date:** 2026-09-20
- **Supersedes:** open decision D-007 for the *initial* runtime only

## Context

Ollama is already installed on the M3 Air (empty model store, wildcard listen). The Studio is the intended serving host. MLX is the Apple-native path for training/experimentation but is not the first HTTP API the harness will call.

## Decision

Initial local inference API is **Ollama on the Studio**. Model pulls are explicit (`docs/runbooks/adding-a-model.md`). MLX/MLX-LM live in `models/mlx/` for experiments and future serving. vLLM is not planned (no NVIDIA host).

The Air wildcard listen is finding F-003 (ADR 0029), not the lab serving path. Studio Ollama listens on all interfaces so LAN and Tailscale clients share one process (ADR 0041). Do not publish port 11434.

## Consequences

- First Studio bootstrap installs Ollama via Brewfile but does not pull weights.
- Compatibility of Ollama on M5 Max is unverified until first Studio preflight.

## Alternatives considered

- MLX-LM OpenAI-compatible server first — possible later; more moving parts.
- llama.cpp only — overlapping with Ollama for day one.
