Canonical lab hosts are `m1-mini`, `studio`, and `m3-air`. Everything below is still adjacent-only (D-005).

# Adjacent systems

Systems that share hardware or LAN with the AI lab but are **not** assumed to be AI-lab hosts (ADR 0007, open decision D-005).

Collected 2026-09-19. No addresses committed.

## Sibling product repositories

Present next to this repo in the parent workspace, each with its own Git remote:

- Clarion (Dentro) — network identity / Calyx agents; Docker stack running on the workstation
- Oryntra — local review-room / MCP product
- VolexSwarm — autonomous trading agents (separate stack when running)
- CMDB, IoTFun, mab-registration, notebookllm-ingest, Aegis, others

These remain independent repositories.

## Clarion lab VMs

SSH config on the operator workstation defines aliases `clarion-backend`, `clarion-frontend`, and `clarion-db` on a private `192.168.10.0/24` network, plus a wildcard for that LAN. They are product VMs. Do not treat them as inference hosts unless D-005 says so.

## Shared daemons on the workstation

Not owned by this repo:

- Clarion Docker compose stack (gateway, AI service, Vault, Neo4j, Redis, NATS, Postgres via pgbouncer, workers)
- Agentic factory containers (orchestrator, PR watchdog, factory-status, Vault)
- Host PostgreSQL listening on all interfaces
- Host Ollama (lab-relevant, but not yet configured from this repo)
- **DefenseClaw** on the Air (`~/.defenseclaw`, CLI 0.8.10 as of 2026-09-24) — operator
  governance, **not** owned by this repo. Observed: connectors **antigravity** +
  **cursor** both `mode=action`, `fail-mode=open`; hooks in `~/.cursor/hooks.json`
  (IWO-045). Do not commit `config.yaml` / `device.key` / audit DB.

## Candidates under evaluation (not absorbed)

These are **not** lab hosts yet. Adding any of them needs an IWO + (for
absorbing product stacks) a new ADR. ADR 0025 still applies.

| Candidate | What it is | Fit in ai-lab | First step |
|-----------|------------|---------------|------------|
| **agentic-factory** | Adjacent Air Docker stack (orchestrator / PR watchdog / Vault) | Stay **adjacent**; optional FEAT-007 bridge only | Inventory + boundary doc; never reuse factory Vault |
| **DefenseClaw** (on Air) | Governance gateway: scan MCP/skills, hook agents, audit | Keep on **Air**; Cursor + Antigravity wired (IWO-045) | IWO-046: scan lab MCP before trust |
| **Antares** ([fdtn-ai/antares-1b](https://huggingface.co/fdtn-ai/antares-1b) / [350m](https://huggingface.co/fdtn-ai/antares-350m)) | Cisco Foundation AI vuln-localization terminal agents (Granite 4.0) | **Studio** inference + sandboxed agent loop (not general chat) | Prefer **1B** on Studio; optional **350M** as lighter/draft; no pull until authorized |

Unhealthy Clarion containers were visible at collection time. That is product hygiene, not a Phase 0 task for `ai-lab`.
