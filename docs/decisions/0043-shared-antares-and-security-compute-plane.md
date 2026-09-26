# ADR 0043 — Shared Antares service and external Security Compute Plane

- **Status:** Proposed amendment
- **Date:** 2026-09-26
- **D-020 (2026-09-26):** The operator's Security Compute hypervisor is Proxmox, Intel i7, 64 GB memory, empty. No hostname or endpoint is recorded. This note does not authorize a connection.
- **Amends:** ADR 0040
- **Related:** ADR 0017, 0018, 0020, 0025, 0037, 0040; FEAT-014, FEAT-015, FEAT-017, FEAT-018, FEAT-019, FEAT-020

## Context

AI Lab already has Antares-1B running on the Mac Studio for vulnerability
localization and DefenseClaw operating on the MacBook Air. The operator also
develops software directly on the Air and wants Antares available outside the
AI Lab browser experience.

Separately, AI Lab needs a malware/security-analysis environment. Existing
container isolation is intentionally not malware-grade. The operator has
external virtualization capacity on ESXi and/or Proxmox that is a better trust
boundary for hostile workloads.

The MacBook Air remains the human/development workstation. It must not become a
required transit or infrastructure node for AI Lab services.

## Decision

### 1. Antares is a shared software-security service

Antares remains hosted on the Mac Studio, but it is no longer modeled as only a
Security-page localization job.

The service exposes bounded interfaces for:

- changed-file / diff review
- repository snapshot review
- CWE-oriented vulnerability localization
- code-security findings suitable for IDE, CLI, API, and MCP clients

Consumers may include:

- Cursor and other IDEs on the MacBook Air
- an `antares` CLI client
- AI Lab Agent Studio
- AI Lab coding/security agents
- future MCP-aware development tools

Source transferred from a client is staged in a temporary read-only workspace,
analyzed, and removed according to retention policy.

Antares does not receive repository write access and does not auto-remediate.

### 2. Add a Security Compute Plane

Untrusted executable analysis runs on an external hypervisor, not directly on
the Mac Studio, Mac mini, or MacBook Air. The operator's live provider is
Proxmox (D-020). The adapter may still describe an ESXi path, and that path
has no host.

The Security Compute Plane provides:

- clean VM templates
- ephemeral analysis clones
- snapshot / revert
- Windows and Linux analysis guests
- isolated analysis networks
- optional simulated Internet services
- packet capture
- evidence export
- deterministic teardown

The malware-analysis network must not have a route to:

- the Tailscale tailnet
- AI Lab control-plane services
- the home/management LAN
- production or adjacent product networks
- the public Internet unless a specific, approved controlled-egress experiment
  is defined

### 3. Security agent owns lifecycle orchestration

A dedicated `security` agent is added to the AI Lab harness.

The security agent may manage approved hypervisor workflows through narrow tools
or an MCP service. Its duties include:

- discover allowed templates and pools
- validate template state
- request ephemeral clone creation
- attach the approved isolated network
- boot and wait for guest readiness
- run benign validation fixtures
- start analysis jobs after approval
- collect logs, process/network evidence, and artifacts
- verify expected controls
- revert or destroy ephemeral guests
- report residual resources and validation failures

The agent must use explicit allowlists for:

- hypervisor hosts
- datastores / storage pools
- VM templates
- networks / port groups / bridges
- operations
- guest tools

### 4. Security agent permission boundaries

Read-only inventory, health, and validation may run without per-operation human
approval when policy allows it.

The following are privileged and require approval unless a later ADR creates a
more specific bounded automation policy:

- creating or deleting persistent templates
- changing hypervisor networking
- changing firewall / virtual-switch policy
- changing host configuration
- attaching a VM to a non-analysis network
- enabling real Internet egress
- executing an untrusted sample
- exporting a suspicious executable out of the analysis zone
- changing credentials or secrets
- granting the agent broader hypervisor permissions

### 5. Host responsibilities

| Plane | Host | Responsibility |
|------|------|----------------|
| Human | MacBook Air | IDE, CLI, browser, approvals; optional local DefenseClaw endpoint protection/governance |
| Control | Mac mini | durable state, orchestration, security API, policy, approvals, findings |
| AI Compute | Mac Studio | Ollama, Antares, Jupyter, trusted analysis/model workers |
| Security Compute | Operator Proxmox (D-020) | hostile-workload VMs, isolated networks, snapshots, analysis tooling |

The Air is not a gateway or required data path.

## Consequences

- FEAT-015 should be expanded to describe Antares as a shared service.
- FEAT-018 defines the broader AI security platform.
- FEAT-019 defines Cybersecurity Vise.
- FEAT-020 defines the security-compute agent and hypervisor lifecycle.
- A new hypervisor adapter/MCP service is required.
- Security findings and evidence should flow into the existing AI Lab security
  and observability models rather than creating a separate logging stack.
- Malware-grade execution is prohibited on the Mac hosts.

## Alternatives considered

### Run malware in containers on the Studio

Rejected. Existing AI Lab policy correctly says containers are not
malware-grade isolation.

### Give the security agent full hypervisor administrator access

Rejected. The agent receives narrowly scoped lifecycle operations and cannot
silently change host/network security boundaries.

### Keep Antares only behind `/antares`

Rejected. The operator develops on the Air and needs the same service from IDE,
CLI, and agent workflows.

### Install Antares separately on every development workstation

Rejected as the default. Central Studio inference provides one maintained model
and policy surface. Local clients remain possible later.
