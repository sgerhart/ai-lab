# ADR 0019 — Ollama as initial local inference

- **Status:** Accepted
- **Date:** 2026-09-20
- **Supersedes:** open decision D-007 for the *initial* runtime only

## Context

Ollama is already installed on the M3 Air (empty model store, wildcard listen). The Studio is the intended serving host. MLX is the Apple-native path for training/experimentation but is not the first HTTP API the harness will call.

## Decision

Initial local inference API is **Ollama on the Studio**. Model pulls are explicit (`docs/runbooks/adding-a-model.md`). MLX/MLX-LM live in `models/mlx/` for experiments and future serving. vLLM is not planned (no NVIDIA host).

Ollama must not listen on `*:11434` across all interfaces. Target: Tailscale or loopback. The Air's current wildcard listen is finding F-003 and is not the Studio design.

## Consequences

- First Studio bootstrap installs Ollama via Brewfile but does not pull weights.
- Compatibility of Ollama on M5 Max is unverified until first Studio preflight.

## Alternatives considered

- MLX-LM OpenAI-compatible server first — possible later; more moving parts.
- llama.cpp only — overlapping with Ollama for day one.
