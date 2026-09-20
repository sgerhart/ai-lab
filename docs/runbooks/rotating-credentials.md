# Rotating credentials

**Prerequisites:** Access to the secret store / M1 env file. D-006 still open.

**Effects:** Invalidates old Postgres/Redis/Qdrant/API/cloud keys.

**Steps:** Generate new secrets off-Git. Update gitignored env. Recreate containers (`up -d` recreates if env changes). Rotate cloud LLM keys at the vendor. Rotate Tailscale auth keys if leaked. Record finding without values.

**Verify:** Clients connect with the new secret; old secret fails.

**Rollback:** Keep the previous secret in the store until verification succeeds, then destroy it.
