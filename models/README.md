# Models

Catalog only. **No weights in Git. No automatic downloads.**

| Path | Purpose | Maturity |
|------|---------|----------|
| [catalog.json](catalog.json) | Machine-readable index | Empty of models |
| [catalog.md](catalog.md) | Human table | Mirrors JSON |
| [inference/](inference/README.md) | Ollama bind notes | Encoded, not applied |
| [mlx/](mlx/README.md) | uv project stub | Planned runtime |
| [training/](training/README.md) | uv stub; `scripts/train.sh` refuses | No experiment authorized |
| [datasets/](datasets/README.md) | Pointers, not data | Planned |
| [evaluations/](evaluations/README.md) | Fixture + harness dry-run | FakeBackend only |

Harness smoke (not a model quality claim):

```bash
./scripts/eval-dry-run.sh
./scripts/eval-dry-run.sh --pull    # exits 2
./scripts/train.sh                  # exits 2
```
