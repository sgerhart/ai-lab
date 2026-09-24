# Work orders

This directory holds:

1. **historical implementation-phase records** (`WO-000`–`WO-007`) from the initial repository build.
2. **Protocol Implementation Work Orders** (`IWO-*`) written to the
   [Work Order Protocol](../work-order-protocol/README.md) template
   ([`templates/WO-template.md`](../../templates/WO-template.md)).

They are **not**:

- Live PostgreSQL runtime work orders on `mac-mini` (those are UUIDs via `POST /v1/work-orders`)
- Future capability specs (see [`../features/`](../features/README.md), `FEAT-001`…)

Do not silently rename historical files into `FEAT-*` IDs. New engineering
tasks should use `IWO-…` Markdown here and/or a GitHub issue from the Work
order template. Agent front door: [`AGENT_PROCESS.md`](../../AGENT_PROCESS.md).

| ID | Title | Code in Git | Host deployed | Live verified |
|----|-------|-------------|---------------|---------------|
| [WO-000](WO-000-phase-0-repository-foundation.md) | Foundation | Yes | n/a | n/a |
| [WO-001](WO-001-phase-1-host-bootstrap.md) | Host bootstrap + network | Yes | **Partial** — M1 `--apply` + Air/mini on tailnet; Studio **not** | Mini SSH/Tailscale verified from Air |
| [WO-002](WO-002-phase-2-control-plane.md) | Control-plane compose | Yes | **Yes** — Colima compose on `mac-mini` | Healthchecks + first iCloud dump; **live restore untested** |
| [WO-003](WO-003-phase-3-compute.md) | Studio compute tooling | Yes | **Partial** — Jupyter + Ollama LaunchAgents on `mac-studio` | Lab connect + Agents Ollama live |
| [WO-004](WO-004-phase-4-harness.md) | Agent harness | Yes (unit + ephemeral Postgres) | **Partial** — API on `mac-mini:8088` | `/agents` chat + tool loop via Studio Ollama |
| [WO-005](WO-005-phase-5-agents.md) | Three agents | Yes (deterministic plans) | **No** Studio worker | Plans tested in CI/laptop; not LLM |
| [WO-006](WO-006-phase-6-model-lab.md) | Training/eval | Catalog + refuse-pull | **No** | No weights / no pulls |
| [WO-007](WO-007-phase-7-hardening.md) | Hardening / recovery | CI + throwaway restore | Backup dest iCloud | First `--execute` dump written; restore drill **not** done |

## Protocol IWOs

| ID | Title | Status |
|----|-------|--------|
| [IWO-001](IWO-001-adopt-work-order-protocol.md) | Adopt Work Order Protocol | Complete (docs) |
| [IWO-002](IWO-002-agent-run-conversation-contract.md) | Agent-run / conversation contract | Complete (unit-tested) |
| [IWO-003](IWO-003-authenticated-agent-ui.md) | Authenticated agent UI | Complete |
| [IWO-004](IWO-004-model-router.md) | Model router | Complete |
| [IWO-005](IWO-005-bounded-model-tool-loop.md) | Model/tool loop | Complete |
| [IWO-006](IWO-006-durable-async-recovery.md) | Durable async recovery | Complete |
| [IWO-007](IWO-007-tool-action-approvals.md) | Tool action approvals | Complete |
| [IWO-011](IWO-011-studio-jupyter-host.md)–[015](IWO-015-jupyter-sample-notebook.md) | Studio Jupyter track | Host path live; docs Draft |
| [IWO-016](IWO-016-lab-site-connect-hub.md) | Lab site connect hub | Complete (live) |
| [IWO-017](IWO-017-vault-scaffold.md) | Vault compose scaffold | Complete (not deployed) |
| [IWO-018](IWO-018-browser-api-key-entry.md) | Browser API key entry | Complete (file store) |
| [IWO-019](IWO-019-studio-ollama-provider.md) | Studio Ollama on mini router | Complete (live) |
| [IWO-020](IWO-020-live-ollama-agent-loop.md) | Live Ollama agent tool loop | Complete (live) |
| [IWO-021](IWO-021-cloud-provider-adapters.md) | OpenAI/Anthropic from secrets | Complete (gated; no live $) |
| [IWO-024](IWO-024-personal-agent-studio-shell.md) | Personal Agent Studio shell | Complete |
| [IWO-025](IWO-025-conversation-attachments.md) | Attachments | Complete |
| [IWO-026](IWO-026-personal-agent-definitions.md) | Agent definitions | Complete |
| [IWO-027](IWO-027-mcp-client-allowlist.md) | MCP client allowlist | Complete (stub → listed by IWO-029) |
| [IWO-028](IWO-028-deep-research-mode.md) | Deep research mode | Complete (gated) |
| [IWO-029](IWO-029-live-mcp-stdio-transport.md) | Live MCP stdio transport | Complete (unit) |
| [IWO-030](IWO-030-personal-agent-scheduler.md) | Personal agent schedule tick | Complete (unit; no host timer) |
| [IWO-031](IWO-031-background-agent-run-worker.md) | Background agent-run worker | Complete (unit) |
| [IWO-040](IWO-040-retrieval-api.md) | Retrieval API + citation policy | Complete (unit; Qdrant optional) |
| [IWO-042](IWO-042-lab-mcp-server.md) | Lab MCP server for IDEs | Complete (unit) |

Forward-looking capabilities: [`../features/index.md`](../features/index.md).  
Protocol adoption: [`../work-order-protocol/`](../work-order-protocol/README.md).  
Mini-first plan: [`../features/PLAN-mini-first.md`](../features/PLAN-mini-first.md).
