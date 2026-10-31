# ADR 0005 — Network Security, Egress Control, and Trust Boundaries

- **Status:** Accepted (WO-00)
- **Date:** 2026-10-30
- **Context:** `ai-lab/coding-training/`
- **Related:** `docs/decisions/0012-tailscale-private-connectivity.md`, `0017-agent-execution-isolation.md`, `0043-shared-antares-and-security-compute-plane.md`

## Context

The coding-training platform interacts across multiple zones: developer workstation (`mac-air`), control plane (`mac-mini`), model compute (`mac-studio`), and an untrusted execution environment (Linux Sandbox VM on Proxmox). Without strict network zoning, untrusted code could perform SSRF attacks, access host metadata services, scan private tailnet endpoints, or attempt external data exfiltration.

## Decision

1. **Air-Gapped Sandbox Execution:**
   - The Linux Sandbox Worker VM connects only to a dedicated non-routable host bridge on Proxmox.
   - The VM has **zero default gateway** to the Internet and no route to the Tailscale subnet (`100.64.0.0/10`) or local management LAN.
   - The container jail inside the VM is spawned with `--net=none`, blocking all network stack creation.

2. **Controller-to-Worker Transport:**
   - Worker communication with the Mac Mini controller occurs over a single dedicated, firewalled internal port.
   - The worker may poll or accept jobs only with a pre-shared cryptographic HMAC / bearer token scoped strictly to the `sandbox-worker` role.
   - The worker has no direct access to PostgreSQL, Redis, or the Mac Studio.

3. **Mac Studio Model Worker Transport:**
   - Model inference and training APIs on `mac-studio` bind exclusively to the Tailscale interface (`100.64.198.100`) or loopback.
   - Mutual token authentication (`X-AI-Lab-Token`) protects model endpoints.

4. **Negative Security Gate Requirement (Gate WO-03):**
   - Before any LLM-generated code executes, an automated suite of negative penetration tests must pass:
     1. Internal egress attempt to Mac Mini (`100.80.117.123:8088`), Mac Studio (`100.64.198.100:11434`), and Postgres (`5432`) is dropped.
     2. External egress attempt to public IP / DNS (`8.8.8.8:53`) is dropped.
     3. Filesystem traversal to `/etc/shadow`, Docker socket, or host mounts is blocked.
     4. Process exhaustion (fork bomb) and memory flooding are constrained by cgroups.

## Consequences

- The platform maintains complete defense-in-depth even if a model produces sophisticated hostile exploit code.
- Operator verification is required before live execution is enabled on the worker.
