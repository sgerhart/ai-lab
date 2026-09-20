# Model template

When a model is pulled or a cloud alias is approved, add a row to `../catalog.md` and optionally a directory `models/<id>/README.md` with:

- Catalog id
- Upstream source (Hugging Face repo, Ollama library name, API name)
- License
- Approximate disk size
- Backend (`ollama`, `llama.cpp`, `vllm`, `cloud`)
- Host that stores the weights
- Intended agents
- Notes (context length, tool-use quality)

Do not commit the weight file.
