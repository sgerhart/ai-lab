# Model template

When a model is pulled or a cloud alias is approved, add an object to `../catalog.json` (and a row in `../catalog.md`) and optionally a directory `models/<id>/README.md` with:

- Catalog id
- Upstream source (Hugging Face repo, Ollama library name, API name)
- License
- Approximate disk size (record after pull; do not invent)
- Backend (`ollama`, `mlx`, `cloud`)
- Host that stores the weights (`studio`)
- Intended agents
- Notes (context length, tool-use quality)

`pull_authorized` stays `false` in Git. Do not commit the weight file. vLLM is not in scope (no NVIDIA host).
