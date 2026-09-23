# Secrets

Names only in Git (ADR 0003). Values: gitignored env, Keychain (ADR 0027), or
**HashiCorp Vault on the mini** (ADR 0039) once the `vault` compose profile is
deployed.

## Compose / control plane

- `POSTGRES_PASSWORD`
- `REDIS_PASSWORD`
- `QDRANT_API_KEY`
- `AI_LAB_API_TOKEN`
- `VAULT_DEV_ROOT_TOKEN_ID` (dev profile only — replace before real keys)

## Vault KV paths (convention, ADR 0039)

| Path | Purpose |
|------|---------|
| `secret/ai-lab/providers/openai` | OpenAI platform API key (`usage_billed_api`) |
| `secret/ai-lab/providers/anthropic` | Anthropic Console API key |
| `secret/ai-lab/providers/gemini` | Google AI / Gemini API key |
| `secret/ai-lab/studio/jupyter_token` | Studio JupyterLab token (also mirrored to `~/.ai-lab/studio-jupyter.token` on mini for `/lab`) |

Until Vault is live, the browser UI at **`/secrets`** writes the same logical
provider keys to `~/.ai-lab/secrets/providers/*.key` (mode 600) on the mini.
GET APIs never return values.

Do **not** reuse Clarion or agentic-factory Vault credentials (ADR 0025).

Enable scaffold (does not start containers by itself):

```bash
docker compose -f infrastructure/compose.yaml -f infrastructure/compose.vault.yaml \
  --env-file infrastructure/compose.example.env --profile vault config
```

Live `up`, init, and unseal require separate owner authorization.

Rotation: [docs/runbooks/rotating-credentials.md](../../docs/runbooks/rotating-credentials.md).
