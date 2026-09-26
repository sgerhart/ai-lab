# Evaluations

Harness-only dry-run lives in `platform` (`ai_lab_platform.eval_dry_run`). The smoke fixture is [fixtures/smoke.jsonl](fixtures/smoke.jsonl).

This is **not** a model quality eval. It uses `FakeBackend`. It will not `ollama pull`, download Hugging Face weights, or call a live Studio daemon.

```bash
./scripts/eval-dry-run.sh
```

The comparison that does call Studio is [model-bench.jsonl](fixtures/model-bench.jsonl). Default is a plan. `--apply` scores the installed tags and does not pull.

```bash
./scripts/model-bench.sh
./scripts/model-bench.sh --apply
```
