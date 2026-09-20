# ADR 0007 — Lab is not a product monorepo

- **Status:** Accepted
- **Date:** 2026-09-19
- **Phase:** 0

## Context

The parent workspace contains Clarion, Oryntra, VolexSwarm, CMDB, and other projects. Some already use Ollama, Vault, and Docker. Copying them into `ai-lab` would mix product source with lab operations and recreate the F-001 blast radius.

## Decision

`ai-lab` describes how those systems may *consume* lab compute. It does not vendor their source. Adjacent hosts used only for product work stay "adjacent" until a human lists them as AI-lab hosts (open decision D-005).

## Consequences

- Agent catalog entries for Calyx or VolexSwarm are pointers plus lab-scope rules, not forks.
- Compose in this repo is for lab services, not a second Clarion stack.
