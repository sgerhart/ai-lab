# Future capabilities index

**Updated:** 2026-09-26  
**Plan:** [PLAN-mini-first.md](PLAN-mini-first.md)  
**GitHub:** [#2](https://github.com/sgerhart/ai-lab/issues/2)–[#10](https://github.com/sgerhart/ai-lab/issues/10); [#11](https://github.com/sgerhart/ai-lab/issues/11) (FEAT-010); [#12](https://github.com/sgerhart/ai-lab/issues/12) (FEAT-011).

## What the lab can do now

Honest snapshot for the operator. Code in Git is not the same as a path exercised live. The New agent screen layout is **not** an accepted product decision ([D-019](../open-decisions.md)).

| Capability | In Git | Live on the lab |
|------------|--------|-----------------|
| Control plane API + LangGraph (`mac-mini:8088`, login) | Yes | Yes |
| Studio chat at `/`. Dashboard and New chat stay fixed. Under the line: Jupyter Labs, Agent Studio, MCP, Security, Configure, then Projects and Chats in one scroll. Search is the icon beside AI LAB and can filter chats by project. The sidebar collapses from the menu button. `/agents` and `/lab` redirect home (IWO-059). Agent Studio is the design canvas (IWO-063) | Yes | Synced to the mini. Live layout pass for Agent Studio is still open (D-019). Live lab-health pass not recorded |
| Model picker from Studio Ollama tags; no silent paid fallback. Models page can assign General, Coding, and Fast. Chat stays on the catalog default until that save | Yes (IWO-055) | Yes. Installed tags seen 2026-09-25: `qwen3.6:35b-a3b` (Q4_K_M), `qwen3.8:27b`, `qwen3-coder:30b`, `llama3.2:3b`. Catalog default is `qwen36-local`. Role assignments live in `~/.ai-lab/model-roles.json` and are not saved until the operator clicks Save. Git catalog `status` stays `catalogued-not-pulled` |
| Standing agents (lab check, research, coding) with optional schedule | Yes | Scheduler LaunchAgent ticks the mini. Create/run screen copy is provisional |
| Coding Assistant reads a workspace; patches and commits only in a separate git worktree after exact approval | Yes (IWO-056, IWO-058) | Unit-tested. Studio can prepare the copy. Operator has not finished a live patch. Push, PR, and tests stay denied |
| Retrieval memory (Qdrant) and gated `memory_write`. A project can index its own Markdown and text files; a chat in that project searches only those (IWO-060) | Yes | Qdrant live on mini. Project-document cite on the live lab not recorded |
| Lab MCP for Cursor on the Air | Yes | Wired (IWO-054) |
| Deep research / cloud models | Gated adapters | Off until `/secrets` authorizes them |
| Studio Jupyter | Host scripts | Up on `:8888` |
| Antares-1B completions, jobs, `/antares` | Yes | UI and services live. Reboot LaunchAgents not set. Repo choice beyond the Studio fixture is direction ([ADR 0040](../decisions/0040-security-plane-gateway-and-antares.md)) |
| Security plane: DefenseClaw summary, billed-API gateway, **Security** as the board | DefenseClaw summary and finding glossary in Git (IWO-061, IWO-062). Gateway not built. The page does not edit DefenseClaw config | DefenseClaw live on the Air. One summary was stored on the mini on 2026-09-25. Repeating that from the Air still needs `~/.ai-lab/api.token` there. The Findings pane was not checked in a browser |
| Studio worker `:8090` | Scripts | Not running |
| Model comparison on short fixtures (IWO-057) | Script, unit tests | First live Studio pass 2026-09-25: the three large tags each scored 4/4. The fixture did not separate them, so Coding Local stays `qwen3-coder:30b` |
| Pull requests from an agent (FEAT-007) | Not started | No |

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
| 3 | [FEAT-012](FEAT-012-lab-site-and-secret-vault.md) | Lab site + Vault (frictionless Studio) | **Partial (live):** Jupyter opens from Studio `/`; `/secrets` `/help`; trusted_tailnet; Vault scaffold only | — |
| 3 | [FEAT-013](FEAT-013-personal-agent-studio.md) | Personal Agent Studio | **Partial:** IWO-024–029 shell/attach/deploy/stdio MCP/deep research | — |
| 4 | [FEAT-003](FEAT-003-studio-worker-and-models.md) | Studio inference and worker | **Partial:** Ollama+Jupyter live; IWO-019 router | [#4](https://github.com/sgerhart/ai-lab/issues/4) |
| 5 | [FEAT-006](FEAT-006-studio-jupyterlab.md) | Studio JupyterLab (direct access first) | **Partial (live):** Studio Lab + MLX/Ollama; Air opens Jupyter from Studio `/` | [#7](https://github.com/sgerhart/ai-lab/issues/7) |
| 6 | [FEAT-005](FEAT-005-python-client-mcp.md) | Python client / IDE MCP | **Partial:** IWO-042 + Cursor (IWO-054) | [#6](https://github.com/sgerhart/ai-lab/issues/6) |
| 7 | [FEAT-008](FEAT-008-research-retrieval-memory.md) | Research + retrieval memory | **Partial:** IWO-040/041 + Qdrant live (IWO-053) | [#9](https://github.com/sgerhart/ai-lab/issues/9) |
| 8 | [FEAT-009](FEAT-009-scheduled-personal-agents.md) | Scheduled personal/lab-ops agents | **Partial:** IWO-030 + LaunchAgent (IWO-052) | [#10](https://github.com/sgerhart/ai-lab/issues/10) |
| 9 | [FEAT-016](FEAT-016-local-coding-models-and-assistant.md) | Local coding models + Coding Assistant | **Partial:** profiles, role overlay, read tools, isolated patch/commit, first bench. PR delivery not started. Agent screen UX open (D-019) | — |
| 9 | [FEAT-007](FEAT-007-coding-agent-pr-workflow.md) | Optional coding-agent / PR workflow | **Partial (plan fixture)** — later write/PR; see FEAT-016 | [#8](https://github.com/sgerhart/ai-lab/issues/8) |
| 9 | [FEAT-014](FEAT-014-defenseclaw-operator-governance.md) | DefenseClaw on Air (operator governance) | **Partial (live):** Cursor+Antigravity action (IWO-044/045) | — |
| 10 | [FEAT-015](FEAT-015-antares-vuln-localization.md) | Antares vuln-localization (Studio) | **Partial** — IWO-047–049 `/antares` UI live | — |
| 3 | [FEAT-017](FEAT-017-agent-operating-studio.md) | Agent Operating Studio | **In progress:** IWO-063 shell in Git. Live layout pass open (D-019) | — |

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
| [IWO-030](../work-orders/IWO-030-personal-agent-scheduler.md) | Personal agent schedule tick | FEAT-009/013 | **Complete** (unit + live tick) |
| [IWO-031](../work-orders/IWO-031-background-agent-run-worker.md) | Background agent-run worker | FEAT-002/010 | **Complete** (unit; mini when DATABASE_URL) |
| [IWO-040](../work-orders/IWO-040-retrieval-api.md) | Retrieval API + citation policy | FEAT-008 | **Complete** (unit; Qdrant live via IWO-053) |
| [IWO-041](../work-orders/IWO-041-memory-write-gates.md) | Agent memory_write gates | FEAT-008 | **Complete** (unit) |
| [IWO-042](../work-orders/IWO-042-lab-mcp-server.md) | Lab MCP server for IDEs | FEAT-005 | **Complete** (unit) |
| [IWO-044](../work-orders/IWO-044-defenseclaw-preflight.md) | DefenseClaw preflight (Air) | FEAT-014 | **Complete** (read-only) |
| [IWO-045](../work-orders/IWO-045-defenseclaw-cursor-connector.md) | DefenseClaw Cursor connector | FEAT-014 | **Complete** (Air action mode) |
| [IWO-046](../work-orders/IWO-046-scan-lab-mcp.md) | Scan lab MCP before Cursor trust | FEAT-014 | **Done** (F-014) |
| [IWO-047](../work-orders/IWO-047-antares-1b-studio.md) | Antares-1B on Studio | FEAT-015 | **Complete** (weights) |
| [IWO-048](../work-orders/IWO-048-antares-completions-sandbox.md) | Antares completions + sandbox | FEAT-015 | **Complete** (loopback :8001) |
| [IWO-049](../work-orders/IWO-049-antares-studio-ui.md) | Antares Studio UI | FEAT-015 | **Complete** (`/antares`) |
| [IWO-052](../work-orders/IWO-052-scheduler-launchagent.md) | Scheduler LaunchAgent on mini | FEAT-009 | **Complete** (live) |
| [IWO-053](../work-orders/IWO-053-wire-qdrant-env.md) | Wire Qdrant into control-plane env | FEAT-008 | **Complete** (live) |
| [IWO-054](../work-orders/IWO-054-cursor-lab-mcp.md) | Wire Cursor to lab MCP | FEAT-005 | **Complete** (Air) |
| [IWO-055](../work-orders/IWO-055-coding-model-profiles-routing.md) | Coding model profiles + Studio routing | FEAT-016 | **Complete** (unit; no pulls) |
| [IWO-056](../work-orders/IWO-056-readonly-coding-assistant.md) | Read-only Coding Assistant | FEAT-016 | **Complete** (unit; no writes on the primary checkout) |
| [IWO-057](../work-orders/IWO-057-model-bench.md) | Studio model comparison | FEAT-016 | **Complete** (unit + one live pass; fixture did not drop the coding profile) |
| [IWO-058](../work-orders/IWO-058-isolated-coding-worktree.md) | Isolated worktree writes | FEAT-016 | **Complete** (unit; approval + worktree only) |
| [IWO-059](../work-orders/IWO-059-chat-first-studio.md) | Chat-first Studio shell | FEAT-013 | **In progress** (code; live operator pass open) |
| [IWO-060](../work-orders/IWO-060-project-documents.md) | Project document library | FEAT-008 | **In progress** (unit; live cite pass open) |
| [IWO-061](../work-orders/IWO-061-defenseclaw-security-summary.md) | DefenseClaw summary on Security | FEAT-014 | **In progress** (unit; one report stored; Air `--apply` still needs a local token) |
| [IWO-062](../work-orders/IWO-062-defenseclaw-finding-glossary.md) | DefenseClaw finding glossary | FEAT-014 | **In progress** (unit; pane not checked in the browser) |
| [IWO-063](../work-orders/IWO-063-agent-studio-shell.md) | Agent Studio shell | FEAT-017 | **In progress** (unit; live layout pass open) |
| [IWO-064](../work-orders/IWO-064-jupyter-ollama-help.md) | Jupyter code help via Studio Ollama | FEAT-006 | **In progress** (6.0.0 on Studio; Air question not asked) |

## Historical phase work orders

`WO-000`–`WO-007` remain under [`../work-orders/`](../work-orders/README.md). Not renamed.
