# IWO-057 — Studio model comparison

**Status:** Complete (first live pass 2026-09-25 did not separate the models)  
**Priority:** P2  
**Feature:** [FEAT-016](../features/FEAT-016-local-coding-models-and-assistant.md)

## What this slice does

`./scripts/model-bench.sh` lists the comparison. `--apply` asks Studio Ollama
to answer four short cases: two general, two coding. Default models are
`qwen3.6:35b-a3b`, `qwen3-coder:30b`, and `qwen3.8:27b`. Context is capped at
4096 tokens so the bench does not take the trained 256K window. It does not
pull weights and it does not change the chat default.

The result says whether one model covers both tracks on this fixture, or the
coding tag still wins its own cases. It is a first signal, not a leaderboard.

## Acceptance

- [x] Unit tests score a correct function and refuse an import
- [x] Operator ran `--apply` on 2026-09-25. `qwen3.6:35b-a3b`, `qwen3-coder:30b`, and `qwen3.8:27b` each passed 4/4. Speed was the only difference. The fixture is too small to drop the coding profile.
