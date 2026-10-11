# AISVS 1.0 Level 1 gap register

**Status:** Written. Not a certification. [ADR 0044](../decisions/0044-adopt-aisvs-level-1.md) is still Proposed.  
**Updated:** 2026-10-05  
**Work order:** [IWO-085](../work-orders/IWO-085-aisvs-level-1-gap-register.md)

This register lists every **Level 1** requirement in OWASP AISVS 1.0 for the lab’s own agents, MCP servers, local models, and retrieval. Requirement sentences stay upstream. Each row cites the identifier and records lab evidence in this repository’s words.

Upstream: [AISVS 1.0](https://github.com/OWASP/AISVS/tree/main/1.0/en). The standard is CC BY-SA 4.0. This tree stays all-rights-reserved ([ADR 0021](../decisions/0021-all-rights-reserved.md)).

A `met` row means the cited control exists. It does not mean the lab passed an audit, and it does not mean ASVS Level 1 was assessed.

## Counts

51 Level 1 identifiers. C5 has none.

| Status | Count |
|--------|------:|
| met | 1 |
| partial | 19 |
| gap | 24 |
| not applicable | 7 |

| Chapter | Level 1 IDs | met | partial | gap | not applicable | Follow-on |
|---------|------------:|----:|--------:|----:|---------------:|-----------|
| C1 Training data | 2 | 0 | 0 | 0 | 2 | none |
| C2 Input validation | 7 | 0 | 1 | 6 | 0 | [IWO-086](../work-orders/IWO-086-aisvs-input-validation.md) |
| C3 Model lifecycle | 3 | 0 | 3 | 0 | 0 | [IWO-087](../work-orders/IWO-087-aisvs-model-admission.md) for 3.1.1 and 3.2.1 |
| C4 Infrastructure | 3 | 0 | 1 | 1 | 1 | [IWO-088](../work-orders/IWO-088-aisvs-model-load-isolation.md) |
| C5 Access control | 0 | — | — | — | — | none at Level 1 |
| C6 Model supply chain | 3 | 0 | 1 | 2 | 0 | [IWO-087](../work-orders/IWO-087-aisvs-model-admission.md) |
| C7 Output control | 5 | 0 | 3 | 2 | 0 | [IWO-089](../work-orders/IWO-089-aisvs-output-controls.md) |
| C8 Memory and vectors | 2 | 0 | 1 | 1 | 0 | [IWO-090](../work-orders/IWO-090-aisvs-embedding-controls.md) |
| C9 Agents | 6 | 1 | 4 | 1 | 0 | [IWO-091](../work-orders/IWO-091-aisvs-agent-bounds.md) |
| C10 MCP | 9 | 0 | 2 | 5 | 2 | [IWO-092](../work-orders/IWO-092-aisvs-mcp-checks.md) |
| C11 Adversarial robustness | 6 | 0 | 1 | 5 | 0 | [IWO-093](../work-orders/IWO-093-aisvs-robustness-evidence.md) |
| C12 Monitoring | 5 | 0 | 2 | 1 | 2 | [IWO-094](../work-orders/IWO-094-aisvs-ai-monitoring.md) |

## How to read a row

| Column | Meaning |
|--------|---------|
| ID | AISVS 1.0 identifier. Open the chapter link for the requirement text. |
| Topic | Short label written here, so the row is readable without pasting the standard. |
| Status | `met`, `partial`, `gap`, or `not applicable` |
| Evidence | Files and work orders in this repo |

## C1 Training data integrity

Chapter: [C1](https://github.com/OWASP/AISVS/blob/main/1.0/en/0x10-C01-Training-Data-Integrity-and-Traceability.md)

The lab consumes models. [WO-006](../work-orders/WO-006-phase-6-model-lab.md) refuses unattended pulls. Project documents are a retrieval corpus ([IWO-060](../work-orders/IWO-060-project-documents.md)), not a training set.

| ID | Topic | Status | Evidence |
|----|-------|--------|----------|
| 1.1.1 | Limit training fields to the model’s purpose | not applicable | No training pipeline |
| 1.2.1 | Access control on a labeling platform | not applicable | No labeling platform |

## C2 Input validation

Chapter: [C2](https://github.com/OWASP/AISVS/blob/main/1.0/en/0x10-C02-Input-Validation.md)

| ID | Topic | Status | Evidence |
|----|-------|--------|----------|
| 2.1.1 | Normalize input before tokenization | gap | No normalizer in the chat or agent path. [IWO-086](../work-orders/IWO-086-aisvs-input-validation.md) |
| 2.1.2 | Detect encoding smuggling | gap | Same |
| 2.1.3 | Screen untrusted steering input | partial | DefenseClaw screens IDE hooks on the Air ([FEAT-014](../features/FEAT-014-defenseclaw-operator-governance.md), [IWO-061](../work-orders/IWO-061-defenseclaw-security-summary.md)). [agent-permissions.md](agent-permissions.md) treats tool results as untrusted text and does not block a prompt. Studio chat has no injection screen. |
| 2.1.4 | Reject over-long input | gap | No pre-window reject. [IWO-086](../work-orders/IWO-086-aisvs-input-validation.md) |
| 2.1.5 | Character allow-list | gap | Same |
| 2.2.1 | Score prompts for harmful content | gap | No content classifier. [IWO-086](../work-orders/IWO-086-aisvs-input-validation.md) |
| 2.2.2 | Check that classifier on other languages | gap | Depends on 2.2.1 |

## C3 Model lifecycle

Chapter: [C3](https://github.com/OWASP/AISVS/blob/main/1.0/en/0x10-C03-Model-Lifecycle-Management.md)

| ID | Topic | Status | Evidence |
|----|-------|--------|----------|
| 3.1.1 | Inventory deployed model artifacts and origin | partial | [docs/models/serving.md](../models/serving.md) and the model-role catalog ([IWO-055](../work-orders/IWO-055-coding-model-profiles-routing.md)). Git still says `catalogued-not-pulled`. There is no admission record of each loaded artifact. [IWO-087](../work-orders/IWO-087-aisvs-model-admission.md) |
| 3.2.1 | Safety and output tests before use | partial | [IWO-057](../work-orders/IWO-057-model-bench.md) scores a short fixture. It is not a safety or output-sanitization suite. [IWO-087](../work-orders/IWO-087-aisvs-model-admission.md) |
| 3.4.1 | Keep AI runtimes off shared environment boundaries | partial | Control, compute, and human planes are separate hosts ([ADR 0009](../decisions/0009-m1-mini-control-plane.md), [ADR 0010](../decisions/0010-studio-compute-plane.md), [ADR 0011](../decisions/0011-m3-air-human-plane.md)). The lab has one environment, not a development stack and a production stack. No follow-on splits those. |

## C4 Infrastructure

Chapter: [C4](https://github.com/OWASP/AISVS/blob/main/1.0/en/0x10-C04-Infrastructure.md)

| ID | Topic | Status | Evidence |
|----|-------|--------|----------|
| 4.1.1 | Run models in isolated sandboxes | partial | Agent isolation tiers are [ADR 0017](../decisions/0017-agent-execution-isolation.md). Studio Ollama is a host service ([ADR 0019](../decisions/0019-ollama-initial-inference.md), [ADR 0041](../decisions/0041-studio-ollama-lan-and-tailscale.md)), not a per-model sandbox. [IWO-088](../work-orders/IWO-088-aisvs-model-load-isolation.md) |
| 4.1.2 | Allow-list safe model serialization formats | gap | No format allow-list at load. [IWO-088](../work-orders/IWO-088-aisvs-model-load-isolation.md) |
| 4.3.1 | Edge devices authenticate to the core | not applicable | No edge or mobile inference device. The Air is the human plane. |

## C5 Access control

Chapter: [C5](https://github.com/OWASP/AISVS/blob/main/1.0/en/0x10-C05-Access-Control-and-Identity.md)

AISVS 1.0 assigns no C5 requirement to Level 1. Agent identity and human approval for privileged tools are still in force ([ADR 0018](../decisions/0018-human-approval-privileged-actions.md), [agent-permissions.md](agent-permissions.md)). Those are not claimed as Level 1 coverage.

## C6 Model supply chain

Chapter: [C6](https://github.com/OWASP/AISVS/blob/main/1.0/en/0x10-C06-Supply-Chain.md)

| ID | Topic | Status | Evidence |
|----|-------|--------|----------|
| 6.1.1 | Scan models for malicious code before import | gap | No import scan. [IWO-087](../work-orders/IWO-087-aisvs-model-admission.md) |
| 6.1.2 | Download weights only from approved sources | partial | [WO-006](../work-orders/WO-006-phase-6-model-lab.md) refuses unattended pulls. Named tags are catalogued. The Studio Ollama daemon is not limited to that list. [IWO-087](../work-orders/IWO-087-aisvs-model-admission.md) |
| 6.2.1 | Publish a machine-readable AI bill of materials | gap | No AI BOM. [IWO-087](../work-orders/IWO-087-aisvs-model-admission.md) |

## C7 Output control

Chapter: [C7](https://github.com/OWASP/AISVS/blob/main/1.0/en/0x10-C07-Model-Behavior.md)

| ID | Topic | Status | Evidence |
|----|-------|--------|----------|
| 7.1.1 | Validate model output against a schema | gap | Free-text chat is shown as returned. [IWO-089](../work-orders/IWO-089-aisvs-output-controls.md) |
| 7.1.2 | Bound output length and stop generation | partial | `RunBudget.max_steps` stops the tool loop (`platform/src/ai_lab_platform/conversation.py`, `agent_loop.py`). A single completion uses the provider limit. [IWO-089](../work-orders/IWO-089-aisvs-output-controls.md) |
| 7.3.1 | Classify and block harmful responses | gap | No response classifier. [IWO-089](../work-orders/IWO-089-aisvs-output-controls.md) |
| 7.4.1 | Attribute retrieval answers to sources | partial | Retrieval refuses invented citations (`retrieval.py`). Grounded chat attaches sources ([IWO-082](../work-orders/IWO-082-grounded-chat.md), `chat_grounding.py`). Chat without sources can still answer. [IWO-089](../work-orders/IWO-089-aisvs-output-controls.md) |
| 7.4.2 | Take attributions from retrieval metadata | partial | The retrieval service fills source fields. The model is told not to invent citations. Nothing checks that a citation string came from those fields. [IWO-089](../work-orders/IWO-089-aisvs-output-controls.md) |

## C8 Memory, embeddings, and vector search

Chapter: [C8](https://github.com/OWASP/AISVS/blob/main/1.0/en/0x10-C08-Memory-Embeddings-and-Vector-Database.md)

| ID | Topic | Status | Evidence |
|----|-------|--------|----------|
| 8.1.1 | Separate vector namespaces per tenant | partial | One operator. A project chat searches only that project’s documents ([IWO-060](../work-orders/IWO-060-project-documents.md)). Qdrant requires an API key ([ADR 0024](../decisions/0024-qdrant-api-key-required.md)). There is no second tenant. [IWO-090](../work-orders/IWO-090-aisvs-embedding-controls.md) |
| 8.2.1 | Drop or mask sensitive fields before embedding | gap | `memory_write` waits for approval ([IWO-041](../work-orders/IWO-041-memory-write-gates.md), `approvals.py`). Nothing scans the text before it is embedded. [IWO-090](../work-orders/IWO-090-aisvs-embedding-controls.md) |

## C9 Agents

Chapter: [C9](https://github.com/OWASP/AISVS/blob/main/1.0/en/0x10-C09-Orchestration-and-Agentic-Action.md)

| ID | Topic | Status | Evidence |
|----|-------|--------|----------|
| 9.1.1 | Per-tool time and resource quotas | partial | HTTP timeouts exist on Ollama, retrieval, and fetch. No per-tool CPU, memory, or disk quota. [IWO-091](../work-orders/IWO-091-aisvs-agent-bounds.md) |
| 9.1.2 | Per-run step, token, and spend budgets | partial | `max_steps` is enforced (API default 8). `max_tokens` and `max_cost_usd` are fields on `RunBudget` and are not enforced. [IWO-091](../work-orders/IWO-091-aisvs-agent-bounds.md) |
| 9.2.1 | Block privileged actions until a human approves | met | [ADR 0018](../decisions/0018-human-approval-privileged-actions.md). `agent_loop.py` returns `approval_required` and does not run the tool. `approvals.py` lists `memory_write` and other privileged names. |
| 9.3.1 | Least-privilege, isolated tools | partial | Each agent has an allowlist ([agent-permissions.md](agent-permissions.md)). Coding writes stay in an isolated worktree ([IWO-058](../work-orders/IWO-058-isolated-coding-worktree.md)). Most tools run in the control-plane process. [IWO-091](../work-orders/IWO-091-aisvs-agent-bounds.md) |
| 9.3.2 | Validate tool outputs against a schema | gap | Tool results stay untrusted text ([agent-permissions.md](agent-permissions.md)). They are not schema-checked. [IWO-091](../work-orders/IWO-091-aisvs-agent-bounds.md) |
| 9.6.1 | Manual switch that stops inference and output | partial | `POST /v1/agent-runs/{run_id}/cancel` and work-order cancel stop the lab run (`agent_loop.py`). They do not stop Studio Ollama mid-generation. [IWO-091](../work-orders/IWO-091-aisvs-agent-bounds.md) |

## C10 MCP

Chapter: [C10](https://github.com/OWASP/AISVS/blob/main/1.0/en/0x10-C10-MCP-Security.md)

| ID | Topic | Status | Evidence |
|----|-------|--------|----------|
| 10.1.1 | Take MCP components from trusted, verified sources | gap | Intake can store a stdio server and leave it unlisted ([IWO-079](../work-orders/IWO-079-mcp-server-intake.md)). The governed allowlist may be empty ([IWO-067](../work-orders/IWO-067-mcp-registry-and-governed-capabilities.md)). Nothing checks a cryptographic signature of the component. [IWO-092](../work-orders/IWO-092-aisvs-mcp-checks.md) |
| 10.2.1 | Validate an access token on each MCP request | partial | The lab API requires a bearer when a token is set ([F-013](overview.md)). Lab MCP is stdio ([IWO-029](../work-orders/IWO-029-live-mcp-stdio-transport.md)), not a token check on each tool call. [IWO-092](../work-orders/IWO-092-aisvs-mcp-checks.md) |
| 10.2.2 | Check token issuer, audience, expiry, and scope | gap | No such check on the stdio path. [IWO-092](../work-orders/IWO-092-aisvs-mcp-checks.md) |
| 10.2.3 | OAuth resource servers must not store access tokens | not applicable | No MCP server in this lab is an OAuth 2.1 resource server |
| 10.3.1 | Authenticated encrypted HTTP for remote MCP | not applicable | No remote MCP server is deployed. HTTP transport is later work ([IWO-029](../work-orders/IWO-029-live-mcp-stdio-transport.md)). |
| 10.3.2 | Allow stdio only on a controlled local host | partial | Stdio is the transport in use, on the Air for Cursor and on trusted hosts for lookup ([mcp-servers.md](../architecture/mcp-servers.md)). The client does not refuse a later remote transport. [IWO-092](../work-orders/IWO-092-aisvs-mcp-checks.md) |
| 10.4.1 | Validate tool-list and tool-call payloads against their schemas | gap | Not checked before the model sees them. [IWO-092](../work-orders/IWO-092-aisvs-mcp-checks.md) |
| 10.4.2 | Screen MCP tool results for indirect prompt injection | gap | DefenseClaw may screen IDE hooks. The lab MCP client does not screen tool results. [IWO-092](../work-orders/IWO-092-aisvs-mcp-checks.md) |
| 10.4.3 | Reject unknown or oversized MCP parameters | gap | No such reject. [IWO-092](../work-orders/IWO-092-aisvs-mcp-checks.md) |

## C11 Adversarial robustness

Chapter: [C11](https://github.com/OWASP/AISVS/blob/main/1.0/en/0x10-C11-Adversarial-Robustness.md)

Antares localizes code weaknesses. Vise is for hostile samples on the external plane. Neither is an evaluation of the chat models.

| ID | Topic | Status | Evidence |
|----|-------|--------|----------|
| 11.1.1 | Use a model that had alignment training | partial | The catalog names published instruction-tuned tags ([docs/models/serving.md](../models/serving.md)). The lab has no alignment evidence for those weights. [IWO-093](../work-orders/IWO-093-aisvs-robustness-evidence.md) |
| 11.1.2 | Re-run an alignment suite on every model change | gap | [IWO-057](../work-orders/IWO-057-model-bench.md) is not that suite and is not run on every tag change. [IWO-093](../work-orders/IWO-093-aisvs-robustness-evidence.md) |
| 11.1.3 | Test models against known adversarial techniques | gap | No such test. [IWO-093](../work-orders/IWO-093-aisvs-robustness-evidence.md) |
| 11.2.1 | Do not return inferred sensitive attributes | gap | No output filter for that. [IWO-093](../work-orders/IWO-093-aisvs-robustness-evidence.md) |
| 11.2.2 | Rate-limit inference against extraction | gap | No per-caller inference rate limit. [IWO-093](../work-orders/IWO-093-aisvs-robustness-evidence.md) |
| 11.3.1 | Detect extraction-style query patterns | gap | No detector. [IWO-093](../work-orders/IWO-093-aisvs-robustness-evidence.md) |

## C12 Monitoring

Chapter: [C12](https://github.com/OWASP/AISVS/blob/main/1.0/en/0x10-C12-Monitoring-and-Logging.md)

General observability stays deferred ([ADR 0026](../decisions/0026-observability-deferred.md)).

| ID | Topic | Status | Evidence |
|----|-------|--------|----------|
| 12.1.1 | Log AI interactions with session context | partial | Agent runs and work orders are stored. The security-event schema is in Git ([IWO-066](../work-orders/IWO-066-common-security-event-and-evidence-model.md)) and is not deployed. Chat prompts and completions are not an audit telemetry stream. [IWO-094](../work-orders/IWO-094-aisvs-ai-monitoring.md) |
| 12.2.1 | Alert on jailbreak and prompt-injection attempts | partial | DefenseClaw posts hook decisions from the Air ([IWO-061](../work-orders/IWO-061-defenseclaw-security-summary.md)). Studio chat has no detector. [IWO-094](../work-orders/IWO-094-aisvs-ai-monitoring.md) |
| 12.3.1 | Detect input drift | gap | No drift monitor. [IWO-094](../work-orders/IWO-094-aisvs-ai-monitoring.md) |
| 12.5.1 | Record dataset lineage through transforms | not applicable | No training datasets. See C1. |
| 12.5.2 | Log labeling activity | not applicable | No labeling activity. See C1. |
