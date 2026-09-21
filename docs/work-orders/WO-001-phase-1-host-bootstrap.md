# WO-001 — Phase 1 host bootstrap and network guidance

**Status:** Repository complete. **Host apply authorized 2026-09-21 but not executed** (this workspace is the M3 Air; SSH to `mac-mini` denied).  
**Phase:** 1

## Acceptance (repo)

- [x] Brewfiles and dry-run setup for m1-mini, studio, m3-air
- [x] Network doc with committed machine names (ADR 0032); tailnet suffix stays in overlay (ADR 0005)
- [x] Preflight script

## Acceptance (deploy — not done)

- [ ] `--apply` on the M1 mini (authorized; blocked: agent is on the Air, `ssh mac-mini` publickey denied)
- [ ] `--apply` on Studio / Air (not authorized this turn)
- [x] Air and mini already on the tailnet as `mac-air` / `mac-mini`. Studio **not** seen on the tailnet 2026-09-21
- [x] F-003 Ollama bind on the Air accepted as workstation risk (ADR 0029)

Do not `--apply --force` the M1 Brewfile on the Air. Do not start control-plane compose on the Air (ADR 0025).
