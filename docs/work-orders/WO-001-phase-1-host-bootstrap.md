# WO-001 — Phase 1 host bootstrap and network guidance

**Status:** M1 data plane **and** FastAPI control plane **up** 2026-09-21 (Tailscale, canonical ports). Docker Desktop uninstalled.  
**Phase:** 1

## Acceptance (repo)

- [x] Brewfiles and dry-run setup for m1-mini, studio, m3-air
- [x] Network doc with committed machine names (ADR 0032); tailnet suffix stays in overlay (ADR 0005)
- [x] Preflight script
- [x] Homebrew 6: `setup.sh` uses `brew bundle install` / `brew bundle check` (no `--dry-run`)

## Acceptance (deploy)

- [x] `--apply` on the M1 mini (packages as `steve`; operator home/SSH `sgerhart`, clone `~/workspace/github/sgerhart/ai-lab`)
- [ ] `--apply` on Studio / Air (not authorized this turn)
- [x] Air and mini already on the tailnet as `mac-air` / `mac-mini`. Studio **not** seen on the tailnet 2026-09-21
- [x] F-003 Ollama bind on the Air accepted as workstation risk (ADR 0029)
- [x] `colima start` on the M1 (`--cpu 2 --memory 3 --disk 40`, Docker context `colima`)
- [x] compose `up` on the M1 (gitignored `compose.local.env`, bind `127.0.0.1`, all three healthy)
- [x] FastAPI / LangGraph control plane on the M1 (`scripts/control-plane.sh`, port **8088**, Tailscale IPv4)
- [x] Quit / uninstall Docker Desktop on the mini; remounted canonical 5432/8088

Do not `--apply --force` the M1 Brewfile on the Air. Do not start control-plane compose on the Air (ADR 0025).
