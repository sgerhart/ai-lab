# Container strategy

- Engine: Colima on the M1 (ADR 0023). Docker Desktop allowed if VM RAM is capped.
- Compose file: `infrastructure/compose.yaml`
- Env template: `infrastructure/compose.example.env`
- Default profile: postgres, redis, qdrant
- Profile `observability`: optional, off
- Image tags are pinned
- Named volumes for data
- Healthchecks required
- `mem_limit` set conservatively
- `restart: unless-stopped`
- Bind `AI_LAB_BIND_ADDRESS` (default 127.0.0.1)

Validate without starting:

```bash
docker compose -f infrastructure/compose.yaml --env-file infrastructure/compose.example.env config
```

`compose.example.env` uses placeholder passwords so `config` can interpolate. Live systems must use a gitignored env with real secrets. The example file's passwords are **not** production credentials; they exist so CI can render the file. A live `up` that still uses the example file is a misconfiguration — preflight should warn.

This workspace has Docker Compose v5.3.1 available on the Air. The M1 engine is unverified.
