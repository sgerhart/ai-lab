# Future capabilities index

**Updated:** 2026-09-23  
**Plan:** [PLAN-mini-first.md](PLAN-mini-first.md)  
**GitHub:** [#2](https://github.com/sgerhart/ai-lab/issues/2)–[#10](https://github.com/sgerhart/ai-lab/issues/10); [#11](https://github.com/sgerhart/ai-lab/issues/11) (FEAT-010); [#12](https://github.com/sgerhart/ai-lab/issues/12) (FEAT-011).

Lifecycle and entities: [README.md](README.md). Template: [TEMPLATE.md](TEMPLATE.md).  
Protocol: [../work-order-protocol/](../work-order-protocol/README.md).

Status legend:

| Label | Meaning |
|-------|---------|
| Idea / Specified | Documented intent only |
| Partial (code/docs/live) | Some progress; see feature file |
| Not started | No meaningful implementation |
| Blocked | Waiting on host or feature |

Do not treat this index as authorized implementation or deploy.

## Priority (mini-first personal-agent platform)

| Pri | ID | Capability | Status | GitHub |
|-----|----|------------|--------|--------|
| 0 | [FEAT-010](FEAT-010-mini-personal-agent-loop.md) | Mini personal-agent loop and harness | **Partial (live):** IWO-020 Studio Ollama tool loop | [#11](https://github.com/sgerhart/ai-lab/issues/11) |
| 0 | [FEAT-011](FEAT-011-frontier-model-access.md) | Frontier model access / provider router | **Partial:** Ollama live; OpenAI/Anthropic gated (IWO-021) | [#12](https://github.com/sgerhart/ai-lab/issues/12) |
| 1 | [FEAT-001](FEAT-001-work-order-planning-and-approval.md) | Feature backlog and WO planning | **Partial (docs)** + protocol IWO-001 | [#2](https://github.com/sgerhart/ai-lab/issues/2) |
| 2 | [FEAT-002](FEAT-002-durable-background-execution.md) | Durable background execution | **Partial (live):** IWO-031 agent-run worker | [#3](https://github.com/sgerhart/ai-lab/issues/3) |
| 3 | [FEAT-004](FEAT-004-agent-chat-and-dashboard.md) | Interactive agent chat UI + dashboard | **Partial (live):** Personal Agent Studio shell | [#5](https://github.com/sgerhart/ai-lab/issues/5) |
| 3 | [FEAT-012](FEAT-012-lab-site-and-secret-vault.md) | Lab site + Vault (frictionless Studio) | **Partial (live):** `/lab` `/secrets` `/help`; trusted_tailnet; Vault scaffold only | — |
| 3 | [FEAT-013](FEAT-013-personal-agent-studio.md) | Personal Agent Studio | **Partial:** IWO-024–029 shell/attach/deploy/stdio MCP/deep research | — |
| 4 | [FEAT-003](FEAT-003-studio-worker-and-models.md) | Studio inference and worker | **Partial:** Ollama+Jupyter live; IWO-019 router | [#4](https://github.com/sgerhart/ai-lab/issues/4) |
| 5 | [FEAT-006](FEAT-006-studio-jupyterlab.md) | Studio JupyterLab (direct access first) | **Partial (live):** Studio Lab + MLX/Ollama; Air opens via mini `/lab` | [#7](https://github.com/sgerhart/ai-lab/issues/7) |
| 6 | [FEAT-005](FEAT-005-python-client-mcp.md) | Python client / IDE MCP | **Specified** | [#6](https://github.com/sgerhart/ai-lab/issues/6) |
| 7 | [FEAT-008](FEAT-008-research-retrieval-memory.md) | Research + retrieval memory | **Partial** | [#9](https://github.com/sgerhart/ai-lab/issues/9) |
| 8 | [FEAT-009](FEAT-009-scheduled-personal-agents.md) | Scheduled personal/lab-ops agents | **Partial:** IWO-030 tick API (no host timer yet) | [#10](https://github.com/sgerhart/ai-lab/issues/10) |
| 9 | [FEAT-007](FEAT-007-coding-agent-pr-workflow.md) | Optional coding-agent / PR workflow | **Partial (plan fixture)** — not core harness | [#8](https://github.com/sgerhart/ai-lab/issues/8) |

## Implementation Work Orders (protocol)

| ID | Title | Feature | Status |
|----|-------|---------|--------|
| [IWO-001](../work-orders/IWO-001-adopt-work-order-protocol.md) | Adopt Work Order Protocol | FEAT-001 | Complete (docs) |
| [IWO-002](../work-orders/IWO-002-agent-run-conversation-contract.md) | Agent-run / conversation contract | FEAT-010 | **Complete** (unit-tested; not live-migrated) |
| [IWO-003](../work-orders/IWO-003-authenticated-agent-ui.md) | Authenticated agent UI | FEAT-004/010 | **Complete** (unit; `/agents`) |
| [IWO-004](../work-orders/IWO-004-model-router.md) | Model router | FEAT-011 | **Complete** (cloud disabled) |
| [IWO-005](../work-orders/IWO-005-bounded-model-tool-loop.md) | Model/tool loop | FEAT-010 | **Complete** (FakeBackend/scripted) |
| [IWO-006](../work-orders/IWO-006-durable-async-recovery.md) | Async recovery | FEAT-002/010 | **Complete** (unit) |
| [IWO-007](../work-orders/IWO-007-tool-action-approvals.md) | Action approvals | FEAT-004/010 | **Complete** (unit) |
| [IWO-011](../work-orders/IWO-011-studio-jupyter-host.md)–[015](../work-orders/IWO-015-jupyter-sample-notebook.md) | Jupyter track | FEAT-006 | Host path live; docs still Draft |
| [IWO-016](../work-orders/IWO-016-lab-site-connect-hub.md) | Lab site connect hub | FEAT-012 | **Complete** (live on mini; trusted_tailnet) |
| [IWO-017](../work-orders/IWO-017-vault-scaffold.md) | Vault compose scaffold | FEAT-012 | **Complete** (compose overlay; not `up`) |
| [IWO-018](../work-orders/IWO-018-browser-api-key-entry.md) | Browser API key entry | FEAT-012 | **Complete** (file store; Vault later) |
| [IWO-019](../work-orders/IWO-019-studio-ollama-provider.md) | Studio Ollama on mini router | FEAT-011/003 | **Complete** (live: llama3.2:3b) |
| [IWO-020](../work-orders/IWO-020-live-ollama-agent-loop.md) | Live Ollama agent tool loop | FEAT-010/003 | **Complete** (live: health_read→FINAL) |
| [IWO-021](../work-orders/IWO-021-cloud-provider-adapters.md) | OpenAI/Anthropic from secrets | FEAT-011 | **Complete** (gated; no live $ in tests) |
| [IWO-024](../work-orders/IWO-024-personal-agent-studio-shell.md) | Personal Agent Studio shell + SSE | FEAT-013/004 | **Complete** |
| [IWO-025](../work-orders/IWO-025-conversation-attachments.md) | Attachments | FEAT-013 | **Complete** |
| [IWO-026](../work-orders/IWO-026-personal-agent-definitions.md) | Personal agent definitions | FEAT-013 | **Complete** |
| [IWO-027](../work-orders/IWO-027-mcp-client-allowlist.md) | MCP client allowlist stub | FEAT-013 | **Complete** (no live transport) |
| [IWO-028](../work-orders/IWO-028-deep-research-mode.md) | Deep research mode | FEAT-013/011 | **Complete** (gated) |
| [IWO-029](../work-orders/IWO-029-live-mcp-stdio-transport.md) | Live MCP stdio transport | FEAT-013 | **Complete** (unit; SSE/HTTP later) |
| [IWO-030](../work-orders/IWO-030-personal-agent-scheduler.md) | Personal agent schedule tick | FEAT-009/013 | **Complete** (unit; host timer later) |
| [IWO-031](../work-orders/IWO-031-background-agent-run-worker.md) | Background agent-run worker | FEAT-002/010 | **Complete** (unit; mini when DATABASE_URL) |

## Historical phase work orders

`WO-000`–`WO-007` remain under [`../work-orders/`](../work-orders/README.md). Not renamed.
