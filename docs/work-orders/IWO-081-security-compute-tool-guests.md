# IWO-081 — Security Compute tool guests

**Status:** Draft  
**Priority:** P0  
**Effort:** L  
**Owner:** human operator, then implementation agent  
**Feature:** [FEAT-019](../features/FEAT-019-cybersecurity-vise.md)  
**Services / Areas:** docs, platform/security

## Problem

Public MCP lists include active scanners and offensive tool wrappers. Those must not run on the Air, the mini, or the Studio. Hosting all of them on one Proxmox server next to trusted lookup MCP would give attack tools a path toward the lab.

## Decision Context

- Chosen approach: Keep this as a contract for later guests on the operator's Proxmox server ([D-020](../open-decisions.md): Intel i7, 64 GB, empty). Tools run inside an ephemeral VM on an isolated network ([D-022](../open-decisions.md)). The mini receives sanitized evidence. Studio does not open a live session to those tools.
- Alternatives rejected: Install the tool catalog on the Proxmox host. Run the FuzzingLabs hub, a Kali image, Nmap, Nuclei, SQLMap, ffuf, masscan, Burp Intruder, or Shodan device search on a Mac. Treat a container on Proxmox as the isolation boundary by itself.
- Assumptions: ADR 0043 stays the direction. Git records the hardware facts only. No hostname, address, or credential.
- Open decisions: D-021, D-022, D-024. Template toolset is operator-supplied. YARA and capa may be part of that toolset later. They are not authorized here.

## What To Build / Fix

Nothing on the Proxmox host. When the operator fills D-021, D-022, and D-024, a later accepted work order can name guest tools. This draft only records the boundary in [mcp-servers.md](../architecture/mcp-servers.md).

## Expected Change Surface

- Expected: this contract and [mcp-servers.md](../architecture/mcp-servers.md)
- Tests: none until a later accepted work order names a guest
- Docs/status: `docs/features/index.md`

## Validation Plan

- Automated: `./scripts/validate-repo.sh`
- Manual: confirm no hostname, address, or image name was invented
- Evidence to include: the architecture page

## Out Of Scope

Powering on a hypervisor, creating a VM, changing a network, installing packages, or executing a sample.

## Do NOT Change

- Do not invent a hostname, address, bridge, or image name.
- No secrets in Git.
- Do not add these servers to the trusted MCP intake.

## Acceptance Criteria

1. Architecture states lookup MCP stays on the trusted hosts. 2. Architecture states active tool MCP waits on an isolated guest on the operator's Proxmox server. 3. This work order does not connect to that server.

## AI Lab gates

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none
- **May run on Air?** Yes — documentation only

## Execution

- **Risk tier:** P0
- **Depends on:** ADR 0043, D-020 (resolved: Proxmox), D-021, D-022, D-024, IWO-072, IWO-073
- **Human verification required:** Yes
- **Project status record:** `docs/features/index.md`

## Closeout

- Verification evidence:
- Host deploy performed? No
