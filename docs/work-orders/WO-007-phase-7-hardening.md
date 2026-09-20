# WO-007 — Phase 7 operational hardening

**Status:** CI, secret scan, live-restore refuse, **throwaway dump→restore tested**. Live M1 restore **not tested**. D-011 destination still open.  
**Phase:** 7

## Acceptance (repo)

- [x] CI validates structure, stdlib tests, LangGraph extras, compose config
- [x] `restore.sh` refuses live overwrite even with `--confirm-restore YES-RESTORE-LIVE`
- [x] Throwaway Postgres restore (`scripts/test-backup-restore.sh`) round-trips a probe row
- [x] `restore-throwaway.sh` refuses non-loopback DSNs, port 5432, and non `ai-lab-pg-*` containers
- [x] `--live` health-check does not treat Air Ollama as the lab

## Acceptance (deploy)

- [ ] Backup destination chosen (D-011)
- [ ] Restore test onto that destination, then a documented live drill
