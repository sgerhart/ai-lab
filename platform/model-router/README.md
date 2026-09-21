Runtime: `../src/ai_lab_platform/model_router.py` (FakeBackend) and `ollama_backend.py` (loopback HTTP, never pulls).

A live Ollama call is not a deploy. Do not point this client at a non-loopback URL until Tailscale bind is documented (D-016).
