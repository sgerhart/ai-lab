# Infrastructure

Control-plane compose for the Mac mini. **Live** on `mac-mini`: Postgres, Redis, and Qdrant. This directory is the Git definition. It does not start containers.

Still open on the host, and not done by the documents here: a restore drill from the iCloud dump onto a non-live database (WO-007), the Vault profile (IWO-017, scaffold only), and the observability profile (ADR 0026, off).

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
