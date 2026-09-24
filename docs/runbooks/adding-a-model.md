# Adding a model

**Prerequisites:** Studio Ollama installed. Disk budget. Human authorization. **Not** part of bootstrap. `scripts/eval-dry-run.sh --pull` will **refuse**.

**Effects:** Downloads weights onto Studio disk.

**Steps:**
1. Copy `models/_template/model.json.example` into `models/catalog.json` with a real `id` and `pull_name`. Leave `pull_authorized` **false**.
2. On Studio, after a human says so, point the CLI at the same bind as `ollama serve`
   (this lab often uses the Tailscale IPv4 — bare `127.0.0.1` then looks “not running”):

```bash
export PATH="/opt/homebrew/bin:$PATH"
export OLLAMA_HOST="$(tailscale ip -4):11434"   # or 127.0.0.1:11434 if that is the serve bind
ollama list
ollama pull <pull_name>
```

3. Record actual size with `ollama list` in the host overlay (`*.local.yaml`), not as a Git claim of `status: pulled`.
4. Optionally map the model into a **profile** in `models/catalog.json` (`profiles[]` + `catalog_model_id`) so Studio labels it (General / Coding / Fast Local). Profiles never pull weights.

**Verify:** `curl -sS "http://$(tailscale ip -4):11434/api/tags"` on Studio (or loopback if that is the bind). From Air/mini: `GET /v1/models` → `choices` lists installed tags.

**Rollback:** `ollama rm <name>`. Catalog object stays or is deleted in the same change. Git still must not say the model is pulled.
