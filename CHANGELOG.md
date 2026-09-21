# Changelog

All notable repository changes. Host deployments are recorded in phase completion docs, not here, until they actually happen.

## Unreleased

### Phase 0–7 repository build (2026-09-20)

- Adopted the three-host architecture: M1 mini control plane, Studio compute plane, M3 Air human plane.
- Kept the repository name `ai-lab`. Relocated Git root remains `ai-lab` (see ADR 0002).
- Added Tailscale-centric network design with placeholders (no real tailnet names or IPs).
- Added host Brewfiles and dry-run setup scripts; compose stack for Postgres, Qdrant, Redis; backup/restore scripts that refuse to overwrite live data without confirmation.
- Added a stdlib-first agent harness (work-order lifecycle, SQLite store for tests, approval gates) and three agent contracts.
- Added a deterministic local worker, loopback HTTP API, and CLI (`scripts/platform.sh`). This is not an LLM loop and not deployed.
- Added CI that validates the repository without tailnet access.
- Added LangGraph as the workflow orchestrator (ADR 0020) with a FastAPI control plane and Studio worker vertical slice (submit → persist → dispatch → approval interrupt → resume). Restart recovery and Studio-unavailable re-queue are unit-tested. **Not deployed.**
- Added `PostgresStore` as the live work-order SoT and `PostgresSaver` checkpoints when `DATABASE_URL` is set. Integration tests use an ephemeral loopback Postgres on port 55432 (not Clarion, not the M1 stack).
- Wired the Studio worker to the three catalog agent plans (shared `agent_plans.py`). Plan failure is persisted as `failed`; Studio-down still re-queues. Still not an LLM and not deployed.
- Added `models/catalog.json`, a FakeBackend eval dry-run, and a train wrapper that refuses pulls and dataset downloads.
- Added a throwaway Postgres dump→restore proof and kept live restore unwired. CI runs the throwaway test.
- Closed lockable defaults as ADRs 0021–0027. MCP is deny-unlisted with zero servers. Ollama client is loopback-only and refuses pulls. Repo-complete checklist: `docs/phases/repo-complete.md`.

### Owner decisions 2026-09-21 (ADRs 0028–0033)

- GitHub stays public (ADR 0028). Alias-only inventory still binds (ADR 0005).
- Air Ollama `*:11434` accepted as workstation risk (ADR 0029); Studio still loopback/Tailscale.
- Backup destination is iCloud Drive (ADR 0030). `backup.sh --execute` refuses non-iCloud targets unless `--allow-other-target`. Live restore still untested.
- M3 Air unified memory attested at 16 GB (ADR 0031).
- Tailscale machine names: `mac-mini`, `mac-studio`, `mac-air` (ADR 0032). Tailnet suffix stays in gitignored overlay (not a GitHub org name).
- Studio Thunderbolt NVMe deferred; initial setup uses the internal 1 TB SSD (ADR 0033).
- `local.inventory.yaml` is now gitignored (the old `*.local.yaml` pattern did not match that filename).
- M1 `--apply` (Brewfile) ran on `mac-mini` as `steve` on 2026-09-21. Colima started the same day (`2` CPU / `3` GiB / `40` GiB). Compose is healthy on canonical ports (loopback + Tailscale IPv4). FastAPI/LangGraph is on Tailscale port **8088** (PostgresStore). Docker Desktop was uninstalled. `host-setup.sh` uses Homebrew 6 `brew bundle install` / `check`.
- ADR 0034: bind loopback or this host's `tailscale ip -4`, never `0.0.0.0`.
- ADR 0035: operator clones live at `$HOME/workspace/github/sgerhart/ai-lab`. Sibling GitHub-account directories stay out of this tree.
- Control-plane `GET /` is an HTML status board (services + work-order counts). `/health` JSON is unchanged.
- First iCloud `backup.sh --execute` on `mac-mini` (2026-09-21). `docker-compose` fallback for hosts without the Compose plugin. LaunchAgent `com.ai-lab.control-plane`.
