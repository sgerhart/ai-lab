# F-015 — Studio SSH authentication failure

- **Date:** 2026-09-24 (updated same day)
- **Hosts:** Air / mini → `mac-studio`
- **Severity:** Low (resolved for Air; mini→Studio fixed 2026-09-24)
- **Status:** Closed (mitigated)

## Summary

Lab hosts do **not** share one login name:

| Host | Operator account |
|------|------------------|
| `mac-mini` | `sgerhart` |
| `mac-studio` | `stevengerhart` |
| `mac-air` | `stevengerhart` |

Earlier probes used `sgerhart@mac-studio`, which correctly fails (wrong account).

**Verified:**

- Air → `stevengerhart@mac-studio`: publickey OK.
- Mini → `stevengerhart@mac-studio`: publickey OK after appending mini’s
  `id_ed25519.pub` (`sgerhart@gmail.com`) to Studio
  `~stevengerhart/.ssh/authorized_keys` (2026-09-24).

## Impact (historical)

Wrong-user probes and missing mini→Studio trust blocked shell ops; Ollama/Jupyter
HTTP were never affected.

## Mitigation applied

1. Document correct usernames in `hosts/README.md`.
2. Trust mini’s ed25519 pubkey on Studio `stevengerhart` account.
3. Keep password SSH disabled on the tailnet.

## Related

FEAT-015, IWO-047, `scripts/antares-preflight.sh`, hosts runbooks
