# Secrets

Names:

- `POSTGRES_PASSWORD`
- `REDIS_PASSWORD`
- `QDRANT_API_KEY`
- optional cloud LLM keys
- future agent API token

Values: gitignored env file on the M1, or D-006 store. Never commit them.

Rotation: [docs/runbooks/rotating-credentials.md](../../docs/runbooks/rotating-credentials.md).
