# Adding a model

**Prerequisites:** Studio Ollama installed. Disk budget. Human authorization. **Not** part of bootstrap. `scripts/eval-dry-run.sh --pull` will **refuse**.

**Effects:** Downloads weights onto Studio disk.

**Steps:**
1. Copy `models/_template/model.json.example` into `models/catalog.json` with a real `id` and `pull_name`. Leave `pull_authorized` **false**.
2. On Studio, after a human says so, talk to the running server. `com.ai-lab.ollama`
   listens on all interfaces (ADR 0041), so loopback works:

```bash
export PATH="/opt/homebrew/bin:$PATH"
export OLLAMA_HOST=127.0.0.1:11434
ollama list
ollama pull <pull_name>
```

3. Record actual size with `ollama list` in the host overlay (`*.local.yaml`), not as a Git claim of `status: pulled`.
4. Optionally map the model into a **profile** in `models/catalog.json` (`profiles[]` + `catalog_model_id`) so Studio labels it (General / Coding / Fast Local). Profiles never pull weights.

**Verify:** `curl -sS http://127.0.0.1:11434/api/tags` on the Studio. From Air or mini, `http://mac-studio:11434/api/tags` and `GET /v1/models` on the mini should list the same tags. A LAN client must be on the Studio subnet.

**Rollback:** `ollama rm <name>`. Catalog object stays or is deleted in the same change. Git still must not say the model is pulled.
