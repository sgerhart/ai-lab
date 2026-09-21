Runtime: `../src/ai_lab_platform/model_router.py` (FakeBackend) and `ollama_backend.py` (loopback HTTP, never pulls).

A live Ollama call is not a deploy. Lab `OLLAMA_HOST` is Studio (`mac-studio`), not the Air (ADR 0029). Loopback until Tailscale bind is set at deploy.
