# Model catalog

Machine-readable source of truth: [`catalog.json`](catalog.json).

No models have been pulled by this repository. Git must not list `status: pulled` or `pull_authorized: true`.

| ID | Backend | Host | Git status |
|----|---------|------|--------|
| `qwen3.6-35b-a3b` | ollama | studio | `catalogued-not-pulled` (live tag `qwen3.6:35b-a3b` on Studio, 2026-09-25) |
| `qwen3.8-27b` | ollama | studio | `catalogued-not-pulled` |
| `qwen3-coder-30b` | ollama | studio | `catalogued-not-pulled` |
| `llama3.2-3b-instruct` | ollama | studio | `catalogued-not-pulled` |

Chat default profile is `qwen36-local`. A live pull does not change these Git statuses.

To add a candidate, copy [`_template/model.json.example`](_template/model.json.example) into `catalog.json` with `pull_authorized` left `false`, then follow [../docs/runbooks/adding-a-model.md](../docs/runbooks/adding-a-model.md) on the Studio after a human authorizes the download.
