# Security plane

**Status:** Direction accepted ([ADR 0040](../decisions/0040-security-plane-gateway-and-antares.md)). Antares jobs and the DefenseClaw summary are the live slices. The API gateway and config editing are not built.  
**Forward direction:** [ADR 0043](../decisions/0043-shared-antares-and-security-compute-plane.md) (proposed) and [security-plane-amendment.md](security-plane-amendment.md). Where they differ from ADR 0040, ADR 0043 is the direction to build. It is not deployed.  
**Updated:** 2026-09-26

AI Lab is the security testing ground for this lab. The mini **Security** page is the board. Each tool keeps running on its own host.

```mermaid
flowchart TB
  subgraph air [mac-air]
    dc["DefenseClaw\nconnectors, alerts, config"]
  end
  subgraph mini [mac-mini]
    sec["Studio Security page"]
    gw["API gateway\ndefault host"]
  end
  subgraph studio [mac-studio]
    ant["Antares-1B\nread-only repo snapshot"]
    oll["Ollama / MLX"]
  end
  vendors["OpenAI / Anthropic / Gemini API"]
  air -->|"summary + confirmed changes"| sec
  air -->|"usage-billed lab calls"| gw
  mini -->|"usage-billed lab calls"| gw
  gw --> vendors
  mini -->|"local chat"| oll
  sec -->|"localization job"| ant
  ant -->|"finding to review"| sec
```

## What each tool is for

| Question | Tool |
|----------|------|
| What is the Air enforcing on Cursor and other connectors, and what are the alerts? | DefenseClaw, summarized on **Security** |
| What are the current DefenseClaw settings, and can I change one? | **Security** shows the masked config. Changing it from the page is not built |
| Should this billed model call be allowed, and where did it go? | API gateway |
| Which files in this repo match a weakness class? | Antares on the Studio |

## API gateway

Foundation API calls (`usage_billed_api`) from the mini and the Air go to one gateway on the tailnet. The default host is the mini. Another tailnet device is allowed only when it is the only host that stores the provider keys.

Local Studio inference does not use the gateway. Chat to Ollama stays `mini → mac-studio`.

Keys stay on the gateway host. The page records allow or deny. Billing classes in [ADR 0038](../decisions/0038-model-provider-billing-classes.md) stay in force.

## DefenseClaw

DefenseClaw stays installed on the Air (`~/.defenseclaw`). The lab does not open `defenseclaw tui` inside the browser. **Security** is the page for status, activity, alerts, and masked configuration.

The Air pushes a summary. If that push stops, the card shows stale. Config files, the device key, and the audit database stay on the Air and out of Git. Finding rows pick up a short explanation from the lab glossary when the page renders them. Each recent block also says whether that step ran and whether the same turn kept going and ended. A turn end means the agent finished a reply. It does not mean the coding task was correct. **Explain with the lab model** rephrases that card. The match text stays on the Air.

## Antares

Antares-1B is the localization model on the Studio. You name a GitHub repository or a snapshot already under `~/.ai-lab/antares/`. A blank weakness class lets Antares choose up to 50 classes for that repository. Named classes stay a narrower review. It returns files a person should review. The live check of the demo tree is the CWE-78 fixture, which points at `app.py`. **Security** opens the form in the Studio shell. `GET /antares` redirects there.

Use it on a repo by placing a read-only copy on the Studio and starting a job. That includes this lab. It also includes an adjacent product such as Clarion: copy the snapshot you want inspected, run the job, review the paths. Clarion’s compose stack, Vault, and repo stay outside this tree ([ADR 0025](../decisions/0025-clarion-adjacent-only.md)).

Antares does not patch the code and does not scan a whole product the way an application scanner would. A broader software scan is a later tool on this same page, not a new meaning for Antares.

## What is live today

| Piece | Live |
|-------|------|
| **Security** page with an Antares badge | Yes |
| Antares jobs and completions on the Studio | Yes. Jobs do not survive reboot until LaunchAgents are set |
| DefenseClaw on the Air | Yes. `com.ai-lab.defenseclaw-report` posts a summary every 10 minutes (2026-09-26). The operator confirmed the Findings pane |
| API gateway | No |
| Choosing an arbitrary repo, including Clarion, from **Security** | No. Jobs use the configured Studio repo path |
| Shared Antares clients, Security Center, Vise, security agent | No. Specified in [ADR 0043](../decisions/0043-shared-antares-and-security-compute-plane.md) |

## Forward direction (ADR 0043)

[security-plane-amendment.md](security-plane-amendment.md) is the direction where it differs from the sections above:

- Antares is a shared software-security service for IDE, CLI, API, and MCP clients. It stays hosted on the Studio.
- The MacBook Air is not a required gateway or infrastructure node.
- Hostile-workload execution is specified for the operator's Proxmox server ([D-020](../open-decisions.md), [FEAT-019](../features/FEAT-019-cybersecurity-vise.md)). The server is an Intel i7 with 64 GB of memory and is empty. Containers and Mac hosts stay prohibited for those workloads.
- Lookup MCP stays on the trusted hosts. It does not wait on that plane. Placement: [mcp-servers.md](mcp-servers.md).

These documents do not authorize a hypervisor connection, VM changes, network changes, or sample execution.

## Verification catalogue

OWASP AISVS 1.0 Level 1 is the proposed checklist for the lab’s own agents, MCP servers, local models, and retrieval ([ADR 0044](../decisions/0044-adopt-aisvs-level-1.md)). Coverage is the gap register [../security/aisvs-level-1.md](../security/aisvs-level-1.md). DefenseClaw, Antares, and Vise stay the tools that register measures. The register does not certify the lab.
