# Model serving design

**Status:** Studio Ollama is live. Git catalog stays `catalogued-not-pulled`.

- Initial runtime: Ollama on the Studio (ADR 0019).
- Control-plane router stores model ids and policies, not weights.
- Pulls are explicit. Bootstrap never pulls. A live `ollama pull` does not change Git `status`.
- Bind: Studio listens on all interfaces (ADR 0041). Lab clients use `http://mac-studio:11434`. Do not publish port 11434.
- Do not serve from the Air.
- MLX is for experiments and future native serving (`models/mlx/`).
- Cloud: optional, work-order gated (ADR 0016).
- Embeddings/rerank: same router interface; specific models TBD when first pulled.

Health (when deployed): `GET http://127.0.0.1:11434/api/tags` on the Studio.
