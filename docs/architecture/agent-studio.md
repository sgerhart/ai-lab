# Agent Studio

**Status:** Shell in Git (IWO-063) and the sidebar label on the mini is Agent Studio. Live operator pass not recorded.  
**Decision:** [ADR 0042](../decisions/0042-agent-studio-operating-platform.md)  
**Feature:** [FEAT-017](../features/FEAT-017-agent-operating-studio.md)

Agent Studio is where agents are designed. Chat at `/` stays the place you talk.
The mini control plane stores the definition and runs it. The Studio host
supplies models. A definition does not care which later runtime executes it.

The studio is for building things, learning, and the work of a product and a
company: files, drafts, decisions, and later mail. A portfolio reader can be
added later and stays read-only until a transfer is approved. Enterprise
systems (ticketing, network policy, IT consoles) can be added later as MCP
connections. They are not the product.

## Agent

```text
Agent = Model + Instructions + Context + Memory + Tools + Skills
        + Workflow + Permissions + Runtime
```

Creating an agent or a workflow is a short conversation. The lab asks what should be done. A known sequence is saved as a workflow with the steps in order. A job that has to decide is saved as an agent, and the lab picks a local model. The operator does not choose a model id, temperature, or quant. When the job needs a catalog MCP server, the build registers that server, plus the skill and the read tools, and leaves the server off. The catalog today is the lab control plane, VirusTotal report reads, keyless CVE lookup, and Gmail. Google sign-in, send, spend, and delete stay with the operator. A connection that is not in the catalog stays listed and is not installed. The runtime still enforces the agent kind
(`coding-assistant`, `research`, `lab-operations`) and the approval gate
(ADR 0018). Builder toggles are intent stored on the definition. They do not
bypass policy.

## Layout

```text
[ AI Lab menu ] [ Agent Studio menu ] [ Canvas ]
```

Both menus collapse. The AI Lab menu is chat, projects, Jupyter, Agent Studio,
MCP, and Security. The Agent Studio menu is the design surface:

Dashboard, My Agents, Templates, Published, Skills, Tools, Knowledge, Memory,
Workflows, Runs, Evaluations, Permissions.

The canvas is where an agent is built. New agent opens the conversation. A saved agent shows what it will do and which local model was chosen. Runs and approvals stay in the canvas column.

## What is real in this slice

| Piece | Now |
|-------|-----|
| Second menu + canvas | In the Studio page |
| Create and update a definition, including a `studio` object | `POST` and `PUT /v1/agent-definitions` |
| Conversation that drafts the agent and chooses the model | Canvas. `POST /v1/agent-studio/draft` |
| Ollama slot | A run or chat continues when its model is already loaded, or when Ollama is idle. A different loaded model keeps the request waiting. The lab does not pull or unload it. |
| Saved fields, including the chosen model | Stored in `studio` |
| Skills library, memory map, workflow patterns, permission classes | Canvas. Handoff, graphs, mail, and portfolio are marked later |
| Native tool list | `GET /v1/capabilities` |
| Isolated copy for a build agent | Existing worktree API, still approval-gated |

## Later

Multi-agent workflows, agent-to-agent handoff, agent-generated UI, a
marketplace, remote runtimes, mail connect, and a read-only portfolio skill.
LangGraph remains the workflow engine (ADR 0020).
