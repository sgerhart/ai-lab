# FEAT-020 — Security Compute Agent

- **Status:** Complete (unit-tested; not deployed)
- **Created:** 2026-09-26
- **Owner:** human (operator)
- **Priority:** Core security automation

## Purpose

Create a dedicated AI Lab security agent that manages and validates the approved
ESXi/Proxmox analysis lifecycle using narrowly scoped tools.

The agent is responsible for repeatability and cleanup. It is not granted
unrestricted hypervisor administration.

## Responsibilities

- discover approved templates
- validate template and snapshot state
- validate isolated-network attachment
- create ephemeral analysis clone
- boot/shutdown
- wait for guest tools/sensor readiness
- run benign validation fixtures
- request approval before untrusted execution
- start bounded analysis workflow
- collect evidence
- validate evidence completeness
- destroy/revert ephemeral VM
- verify residual resources are absent
- produce a signed/structured validation report

## Hypervisor support

Adapter contract must support both:
- VMware ESXi / vSphere-compatible API path
- Proxmox VE API path

Implementation may ship one provider first, but the domain model must not bind
the agent to one vendor.

## Permission classes

### Read
May be auto-approved by policy:
- inventory
- power state
- snapshot state
- datastore capacity
- NIC/network identity
- guest tools readiness
- job artifacts

### Ephemeral lifecycle
Approval-gated initially:
- clone from approved template
- power on/off
- revert approved snapshot
- attach approved analysis network
- delete ephemeral job VM

### Never implicit
- host config
- template mutation
- new privileged credentials
- network/bridge/vSwitch mutation
- firewall mutation
- attach trusted/management networks
- real Internet egress
- untrusted sample execution

## Work Orders

- IWO-076 — security agent definition and policy (Complete; unit-tested)
- IWO-077 — VM lifecycle workflow and validation state machine (Complete; unit-tested)
- IWO-078 — hypervisor test harness and end-to-end benign validation (Complete; unit-tested)

## Acceptance criteria

- [x] Agent can validate environment without changing it
- [x] Agent can execute approved ephemeral lifecycle with full audit
- [x] Failures leave a deterministic cleanup/recovery action
- [x] Hypervisor operations are allowlisted and correlated to a Vise job
- [x] Untrusted execution remains an explicit human approval
