# Changelog

All notable repository changes. Host deployments are recorded in phase completion docs, not here, until they actually happen.

## Unreleased

### Mini / Studio live path (IWO-046–054, IWO-047)

- Scheduler LaunchAgent `com.ai-lab.scheduler-tick` on mini (IWO-052).
- Qdrant wired into control-plane env; `/v1/memory` uses `backend=qdrant` (IWO-053).
- Cursor `ai-lab` MCP on Air; DefenseClaw scan skip recorded as F-014 (IWO-046/054).
- Antares-1B weights + CLI zip on Studio via Jupyter exec; MPS load smoke (IWO-047).
- Studio SSH from Air/mini broken — F-015; Jupyter/Ollama remain reachable.
- Architecture docs refreshed for live control/compute/agent/data flows.

### FEAT-013 / IWO-024–028 — Personal Agent Studio

- ChatGPT-like `/agents` shell: conversation sidebar, SSE streaming chat,
  Studio Ollama default.
- Attachments (PDF/MD/TXT/images) under `~/.ai-lab/uploads/`.
- Personal agent definitions + run; MCP client allowlist stub; deep research
  toggle gated on usage-billed authorize + keys.

### IWO-021 — OpenAI / Anthropic adapters (gated)

- Adapters read keys from `~/.ai-lab/secrets/`; enabled only with usage-billed
  authorize checkbox + key. Gemini remains stub. No live $ in automated tests.

### IWO-020 — Live Studio Ollama agent tool loop

- Policy-aware TOOL/FINAL system prompt; tolerant parser; stop repeated tools.
- `/agents` Run loop shows tool/observation summary (not only raw JSON).
- Live: `lab-operations` + `llama3.2:3b` runs `health_read` then FINAL.

### IWO-019 — Studio Ollama provider on mini router

- `OllamaBackend` allows loopback, `mac-studio`, `*.ts.net`, Tailscale CGNAT.
- `build_router_from_settings` wires live Ollama when `STUDIO_OLLAMA_URL` is set.
- `/agents` chat-first UI: Send completes via model (`reply=true`); defaults to
  enabled Ollama + listed models (prefer `llama3.2`).

### FEAT-012 / IWO-016–018 — lab site, secrets UI, Vault scaffold

- Mini lab site: `/lab`, `/secrets`, `/help`, shared nav; Studio Jupyter open without
  Air-side `ssh -L` (Tailscale bind on Studio).
- `AI_LAB_AUTH_MODE=trusted_tailnet`: Tailscale/loopback peers skip bearer paste.
- Browser write-only API key entry (`~/.ai-lab/secrets/`); usage-billed flag (ADR 0038).
- ADR 0039 HashiCorp Vault on mini; `compose.vault.yaml` scaffold (not deployed).
- Catalog entries for `llama3.2:3b` and MLX 3B 4-bit (Git still `pull_authorized: false`).
- Security finding F-012 (rotate mini API token + DB password).

### Work Order Protocol adoption (IWO-001, ADR 0036)

- Adopted [`dentroio/work-order-protocol`](https://github.com/dentroio/work-order-protocol) Level 1–2 for **implementation** Work Orders.
- Added root `AGENT_PROCESS.md`, `templates/WO-template.md`, expanded GitHub work-order issue template, and `docs/work-order-protocol/` (lifecycle mapping to runtime `Status`, stricter deploy gates).
- Features / IWOs / runtime jobs remain three distinct entities. No host deploy under this change.

### Mini-first personal-agent platform plan (ADR 0037–0038)

- Clarified product intent: always-on personal agents + experimentation on the mini; coding factory optional (FEAT-007).
- Added FEAT-010 (personal-agent loop), FEAT-011 (provider router / billing classes), amended FEAT-002–009, Studio Jupyter milestone-1 track (FEAT-006).
- Bounded IWOs IWO-002–007 (mini) and IWO-011–015 (Jupyter). First code slice: IWO-002. No host deploy or paid API calls in this planning change.

### IWO-002 — conversation / agent-run contract

- Added `conversation.py`, Postgres/SQLite tables, and FastAPI
  `/v1/conversations` + `/v1/agent-runs` endpoints.
- Ordinary chat messages are distinct from durable agent runs and from
  `POST /v1/work-orders`. FakeBackend placeholder traces only; no model/tool
  loop yet (IWO-005). No live mini schema migrate.

### IWO-003–007 — mini-only agent platform (no Studio)

- `/agents` authenticated UI shell (bearer token in sessionStorage).
- Model router with billing classes; OpenAI/Anthropic/Gemini disabled by default.
- Bounded model/tool loop on the mini (`agent_loop.py`) with scripted/FakeBackend tests (≥2 tool steps).
- Cancel / safe retry / reconcile stuck running; action-level approve/deny for privileged tools.
- No host deploy, no Studio, no paid API calls.

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
- Features backlog (`docs/features/`): lifecycle, FEAT-001..009 index, FEAT-001 planning spec; GitHub issues #2–#10. No capability implementation under that docs change.
