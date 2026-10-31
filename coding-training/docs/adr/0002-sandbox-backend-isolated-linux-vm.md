# ADR 0002 — Sandbox Backend and Isolated Linux Execution Environment

- **Status:** Accepted (WO-00)
- **Date:** 2026-10-30
- **Context:** `ai-lab/coding-training/`
- **Related:** `docs/decisions/0017-agent-execution-isolation.md`, `0043-shared-antares-and-security-compute-plane.md`

## Context

Model-generated code is untrusted and potentially hazardous (accidental resource exhaustion, infinite fork loops, intentional or synthetic jailbreak attempts, or network scanning).

AI Lab rules (`AGENTS.md`) strictly forbid executing untrusted code on macOS host workstations (`mac-air`, `mac-mini`, `mac-studio`). Docker on macOS (Colima/Docker Desktop) shares the host kernel or an unhardened developer VM and is not considered a hostile-code boundary.

## Decision

1. **Dedicated Non-Production Linux VM on Proxmox Security Compute:**
   - Host the sandbox execution worker inside a dedicated Linux VM (Ubuntu Server 24.04 LTS or Alpine Linux) running on the external Proxmox hypervisor.
   - The VM connects exclusively to an isolated host-only network bridge with no route to the Tailnet, LAN, Mac hosts, or the public Internet.

2. **Per-Job Disposable Execution Jail:**
   - Inside the Linux worker VM, each candidate code run executes in a disposable, ephemeral sandbox container (rootless Podman or unprivileged `isolate` / Bubblewrap jail).
   - Strict resource boundaries:
     - 1 vCPU hard cap.
     - 512 MiB memory limit with swap disabled.
     - 64 maximum process/thread limit (`pids.max`).
     - Read-only root filesystem with ephemeral `tmpfs` mounts for `/tmp` and workspace.
     - Wall-clock timeout (default 10s) enforced by an out-of-band supervisor.
     - Output truncation: maximum 1 MiB combined stdout/stderr.

3. **Air-Gapped Network Namespace:**
   - The execution container is spawned with `--net=none` (loopback only, zero network interfaces).
   - DNS and socket creation are blocked by seccomp filters.

4. **Out-of-Band Test Runner & Capture:**
   - Trusted test bundles (including hidden edge cases) are mounted read-only into the jail.
   - The test runner executes the candidate against the tests and writes a structured execution summary to an out-of-band pipe.
   - Hidden test source code and expected values are never reflected into standard output or returned to the model.

## Consequences

- Setup requires provisioning and configuring the worker VM on Proxmox.
- The worker daemon communicates with the Mac Mini controller over an authorized point-to-point interface.
- Zero risk of untrusted code escaping onto development or compute Macs.
