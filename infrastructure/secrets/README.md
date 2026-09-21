# Secrets

Names:

- `POSTGRES_PASSWORD`
- `REDIS_PASSWORD`
- `QDRANT_API_KEY`
- optional cloud LLM keys
- future agent API token

Values: gitignored env file on the M1, or macOS Keychain (ADR 0027). Never commit them.

Rotation: [docs/runbooks/rotating-credentials.md](../../docs/runbooks/rotating-credentials.md).
