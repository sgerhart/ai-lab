# Adding a model

**Prerequisites:** Studio Ollama installed. Disk budget. Human authorization. **Not** part of bootstrap. `scripts/eval-dry-run.sh --pull` will **refuse**.

**Effects:** Downloads weights onto Studio disk.

**Steps:**
1. Copy `models/_template/model.json.example` into `models/catalog.json` with a real `id` and `pull_name`. Leave `pull_authorized` **false**.
2. On Studio, after a human says so: `ollama pull <pull_name>`.
3. Record actual size with `ollama list` in the host overlay (`*.local.yaml`), not as a Git claim of `status: pulled`.

**Verify:** `curl -sS http://127.0.0.1:11434/api/tags` on Studio.

**Rollback:** `ollama rm <name>`. Catalog object stays or is deleted in the same change. Git still must not say the model is pulled.
