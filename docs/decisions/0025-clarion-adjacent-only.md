# ADR 0025 — Clarion and other product VMs stay adjacent

- **Status:** Accepted
- **Date:** 2026-09-21
- **Supersedes:** open decision D-005

## Context

The operator workstation runs a product Docker/Postgres stack (Clarion) that already occupies common ports. This lab is not a product monorepo (ADR 0007).

## Decision

Clarion, Oryntra, VolexSwarm, and future app VMs are **adjacent**. They are documented under `docs/inventory/adjacent-systems.md`. This repo must not start control-plane compose on the Air, must not reuse Clarion Vault credentials, and must not claim those stacks as lab services.

## Consequences

- Ephemeral lab tests use ports **55432/55433**, not 5432/6432.
- Absorbing Clarion into the lab requires a new ADR.
