# Model serving design

**Status:** Configuration in Git. **Not deployed. No models pulled.**

- Initial runtime: Ollama on the Studio (ADR 0019).
- Control-plane router stores model ids and policies, not weights.
- Pulls are explicit. Bootstrap never pulls.
- Bind: loopback on Studio for local workers; Tailscale IP if the M1 must call Ollama directly.
- Do not serve from the Air.
- MLX is for experiments and future native serving (`models/mlx/`).
- Cloud: optional, work-order gated (ADR 0016).
- Embeddings/rerank: same router interface; specific models TBD when first pulled.

Health (when deployed): `GET http://127.0.0.1:11434/api/tags` on the Studio.
