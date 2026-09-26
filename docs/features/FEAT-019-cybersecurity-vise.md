# FEAT-019 — Cybersecurity Vise

- **Status:** Partial (job model and fake hypervisor adapter in Git; not deployed)
- **Created:** 2026-09-26
- **Owner:** human (operator)
- **Priority:** Security research

## Purpose

Provide an isolated malware and hostile-artifact analysis capability controlled
from AI Lab while execution occurs on the operator's Proxmox server (D-020), never directly on the
trusted Mac hosts.

## User workflow

1. Submit an artifact or analysis request.
2. Record hashes and metadata before execution.
3. Select an approved analysis profile.
4. Security agent validates the template and isolation state.
5. Security agent creates an ephemeral VM from a clean template.
6. Run preflight/benign validation.
7. Human approves untrusted execution.
8. Execute in isolated VM.
9. Collect evidence.
10. Stop and destroy/revert the ephemeral VM.
11. Verify cleanup.
12. AI Lab indexes findings and evidence for human/AI review.

## Analysis profiles

Initial:
- Windows static + behavioral
- Linux static + behavioral
- source/repository security review via Antares (trusted compute, not malware VM)

Later:
- memory forensics
- document detonation
- browser-oriented analysis
- simulated enterprise services

## Isolation requirements

- no Tailscale inside analysis guests
- no route to AI Lab Mac hosts
- no route to home/management/production LANs
- no real Internet by default
- simulated services are preferred
- separate management and analysis networks
- the analysis guest has one NIC, on the isolated network only
- the security agent stays on the mini and calls the Proxmox API
- credentials used in guests are disposable/non-production
- templates are immutable during jobs

## In Git

`POST /v1/security/vise/jobs` stores a hash, a profile, and a provider name. It refuses sample bytes. Untrusted and behavioral jobs cannot enter `running` without an approval id. `complete` requires `cleanup_status` `verified`. Evidence rows use the IWO-066 locator shape.

The fake adapter runs that lifecycle in memory. The Proxmox and ESXi adapters raise `ProviderNotConfigured` and store no endpoint. These routes are not on the live mini until that process is restarted.

## Work Orders

- IWO-070 — Vise job/API data model
- IWO-071 — hypervisor adapter abstraction
- IWO-072 — isolated network contract
- IWO-073 — base VM template contract
- IWO-074 — evidence collection pipeline
- IWO-075 — Vise UI and job review
- [IWO-081](../work-orders/IWO-081-security-compute-tool-guests.md) — tool guests stay on an isolated VM on the operator's Proxmox server. Does not connect to it.

## Acceptance criteria

- [ ] No malware execution on Mac hosts
- [ ] Job can be proven isolated before execution
- [ ] Ephemeral guest cleanup is verified after job
- [ ] Evidence is indexed without importing guest trust into the control plane
- [ ] Untrusted execution requires approval
