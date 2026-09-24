# Rotating credentials

**Prerequisites:** Access to Keychain / the M1 gitignored env file (ADR 0027).

**Effects:** Invalidates old Postgres/Redis/Qdrant/API/cloud keys.

**Steps:**

### Lab API token + Postgres (F-012)

From Air (SSH to mini configured):

```bash
./scripts/rotate-control-plane-secrets.sh          # dry-run
./scripts/rotate-control-plane-secrets.sh --apply  # when authorized
```

Then on the mini, read `~/.ai-lab/api-token.rotated` (mode 600) and paste into
the Air Studio session. Never commit that file. Prefer not to `cat`
`~/.ai-lab/start-control-plane.sh` in chat.

### General

Generate new secrets off-Git. Update gitignored env. Recreate containers
(`up -d` recreates if env changes). Rotate cloud LLM keys at the vendor.
Rotate Tailscale auth keys if leaked. Record finding without values.

**Verify:** Clients connect with the new secret; old secret fails.

**Rollback:** Keep the previous secret in the store until verification succeeds, then destroy it.
