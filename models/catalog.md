# Model catalog

Machine-readable source of truth: [`catalog.json`](catalog.json).

No models have been pulled by this repository. Git must not list `status: pulled` or `pull_authorized: true`.

| ID | Backend | Host | Status |
|----|---------|------|--------|
| — | ollama | studio | none catalogued for pull |

To add a candidate, copy [`_template/model.json.example`](_template/model.json.example) into `catalog.json` with `pull_authorized` left `false`, then follow [../docs/runbooks/adding-a-model.md](../docs/runbooks/adding-a-model.md) on the Studio after a human authorizes the download.
