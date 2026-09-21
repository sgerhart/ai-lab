# m1-mini — control plane

Confirmed: Mac mini, Apple M1, 16 GB unified, 512 GB disk.

**Does:** Postgres, Qdrant, Redis, harness, backup orchestration.  
**Does not:** large local models.

Clone path: `~/workspace/github/sgerhart/ai-lab` (ADR 0035). Operator login is `sgerhart`.

See [RUNBOOK.md](RUNBOOK.md) for the independently executable bring-up.

```bash
./hosts/m1-mini/setup.sh --preflight
./hosts/m1-mini/setup.sh --dry-run
./hosts/m1-mini/setup.sh --apply    # applied 2026-09-21 as steve
```

Engine: Colima (ADR 0023).

## After packages (authorized deploy only)

1. `colima start --cpu 2 --memory 3 --disk 40`
2. Copy `infrastructure/compose.example.env` to a gitignored file; set passwords.
3. `docker compose -f infrastructure/compose.yaml --env-file <that file> up -d`

Do not run those steps from CI or from this coding agent without authorization.
