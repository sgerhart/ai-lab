# Infrastructure

Control-plane compose and supporting config. **Not started.**

| Path | Purpose |
|------|---------|
| [compose.yaml](compose.yaml) | Postgres, Redis, Qdrant |
| [compose.example.env](compose.example.env) | Interpolation for `compose config` / CI |
| [postgres/](postgres/README.md) | Init SQL |
| [qdrant/](qdrant/README.md) | Notes |
| [redis/](redis/README.md) | Notes |
| [backup/](backup/README.md) | Dump layout |
| [monitoring/](monitoring/README.md) | Optional profile — off |
| [network/](network/README.md) | Bind policy |
| [secrets/](secrets/README.md) | Names only |
| [observability/](observability/README.md) | Pointer |

Live env file: gitignored copy of `compose.example.env` with real passwords. Do not `up` using the example file on a real M1.
