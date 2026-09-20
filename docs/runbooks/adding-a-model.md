# Adding a model

**Prerequisites:** Studio Ollama installed. Disk budget. Human authorization. **Not** part of bootstrap.

**Effects:** Downloads weights onto Studio disk.

**Steps:**
1. Add a row to `models/catalog.md` (id, license, size, backend).
2. On Studio: `ollama pull <name>` (exact name from the catalog).
3. Record size with `ollama list`.

**Verify:** `curl -sS http://127.0.0.1:11434/api/tags` on Studio.

**Rollback:** `ollama rm <name>`. Catalog row stays with status `removed` or is deleted in the same change.
