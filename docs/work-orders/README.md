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
| [IWO-041](IWO-041-memory-write-gates.md) | Agent memory_write gates | Complete (unit) |
| [IWO-042](IWO-042-lab-mcp-server.md) | Lab MCP server for IDEs | Complete (unit) |
| [IWO-044](IWO-044-defenseclaw-preflight.md) | DefenseClaw preflight (Air) | Complete (read-only) |
| [IWO-045](IWO-045-defenseclaw-cursor-connector.md) | DefenseClaw Cursor connector | Complete (Air action) |
| [IWO-046](IWO-046-scan-lab-mcp.md) | Scan lab MCP before Cursor trust | Done (F-014) |
| [IWO-047](IWO-047-antares-1b-studio.md) | Antares-1B on Studio | Complete (weights) |
| [IWO-048](IWO-048-antares-completions-sandbox.md) | Antares completions + sandbox | Complete (loopback :8001) |
| [IWO-049](IWO-049-antares-studio-ui.md) | Antares Studio UI | Complete (`/antares`) |
| [IWO-052](IWO-052-scheduler-launchagent.md) | Scheduler LaunchAgent on mini | Complete (live) |
| [IWO-053](IWO-053-wire-qdrant-env.md) | Wire Qdrant into control-plane env | Complete (live) |
| [IWO-054](IWO-054-cursor-lab-mcp.md) | Wire Cursor to lab MCP | Complete (Air) |
| [IWO-055](IWO-055-coding-model-profiles-routing.md) | Coding model profiles + Studio routing | Complete (unit; no pulls) |
| [IWO-056](IWO-056-readonly-coding-assistant.md) | Read-only Coding Assistant | Complete (unit) |
| [IWO-057](IWO-057-model-bench.md) | Studio model comparison | Complete (unit + one live pass; fixture did not drop the coding profile) |
| [IWO-058](IWO-058-isolated-coding-worktree.md) | Isolated worktree writes | Complete (unit) |
| [IWO-059](IWO-059-chat-first-studio.md) | Chat-first Studio shell | In progress (live lab-health pass open) |
| [IWO-060](IWO-060-project-documents.md) | Project document library | In progress (unit; live cite pass open) |
| [IWO-061](IWO-061-defenseclaw-security-summary.md) | DefenseClaw summary on Security | Complete (Air posts every 10 minutes) |
| [IWO-062](IWO-062-defenseclaw-finding-glossary.md) | DefenseClaw finding glossary | In progress (unit; pane not checked in the browser) |
| [IWO-063](IWO-063-agent-studio-shell.md) | Agent Studio shell | In progress (unit; live layout pass open) |
| [IWO-064](IWO-064-jupyter-ollama-help.md) | Jupyter code help via Studio Ollama | In progress (6.0.0 on Studio; Air question not asked) |
| [IWO-065](IWO-065-security-platform-foundation.md) | Security platform foundation | Complete (unit; not deployed) |
| [IWO-066](IWO-066-common-security-event-and-evidence-model.md) | Common security event and evidence model | Complete (unit; not deployed) |
| [IWO-067](IWO-067-mcp-registry-and-governed-capabilities.md) | MCP registry and governed capabilities | Complete (unit; not deployed) |
| [IWO-068](IWO-068-agent-studio-security-posture.md) | Agent Studio security posture | Draft |
| [IWO-069](IWO-069-security-center-expansion.md) | Security Center expansion | Draft |
| [IWO-070](IWO-070-cybersecurity-vise-job-and-api-model.md) | Cybersecurity Vise job and API model | Complete (unit; not deployed) |
| [IWO-071](IWO-071-hypervisor-adapter-abstraction.md) | Hypervisor adapter abstraction | Complete (unit; fake adapter only) |
| [IWO-072](IWO-072-security-compute-isolated-network-contract.md) | Security Compute isolated network contract | Draft |
| [IWO-073](IWO-073-security-vm-template-contract.md) | Security VM template contract | Draft |
| [IWO-074](IWO-074-vise-evidence-collection-pipeline.md) | Vise evidence collection pipeline | Draft |
| [IWO-075](IWO-075-cybersecurity-vise-operator-ui.md) | Cybersecurity Vise operator UI | Draft |
| [IWO-076](IWO-076-security-agent-definition-and-policy.md) | Security agent definition and policy | Draft |
| [IWO-077](IWO-077-security-vm-lifecycle-and-validation-workflow.md) | Security VM lifecycle and validation workflow | Draft |
| [IWO-078](IWO-078-hypervisor-test-harness-and-benign-end-to-end-validation.md) | Hypervisor test harness and benign end-to-end validation | Draft |
| [IWO-079](IWO-079-mcp-server-intake.md) | MCP server intake | Complete (unit; not deployed) |
| [IWO-080](IWO-080-readonly-third-party-mcp.md) | Read-only third-party MCP candidates | Complete (unit; not deployed) |
| [IWO-081](IWO-081-security-compute-tool-guests.md) | Security Compute tool guests | Draft |

Forward-looking capabilities: [`../features/index.md`](../features/index.md).  
Protocol adoption: [`../work-order-protocol/`](../work-order-protocol/README.md).  
Mini-first plan: [`../features/PLAN-mini-first.md`](../features/PLAN-mini-first.md).
