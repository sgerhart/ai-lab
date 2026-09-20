# WO-006 — Phase 6 SLM / eval / experiments

**Status:** Catalog schema + harness eval dry-run + train refuse. **No weights, no datasets, no training.**  
**Phase:** 6

Do not download datasets or start training.

## Acceptance (repo)

- [x] Machine-readable `models/catalog.json` (empty of pulls)
- [x] Eval dry-run uses FakeBackend and makes no quality claim
- [x] `--pull` / `--download` / `scripts/train.sh` refuse with exit 2
- [x] Git catalog cannot claim `status: pulled` or `pull_authorized: true`

## Acceptance (deploy)

- [ ] Human-authorized first `ollama pull` on the Studio, recorded with real size
- [ ] First real eval against a pulled model
