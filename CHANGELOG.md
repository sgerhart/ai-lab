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
