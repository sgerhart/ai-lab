# ADR 0005 — Public repository inventory boundary

- **Status:** Accepted (until D-001 is resolved)
- **Date:** 2026-09-19
- **Phase:** 0

## Context

`github.com/sgerhart/ai-lab` is public. A useful AI-lab inventory includes RFC1918 addresses, SSH aliases, and hardware serials. Publishing those on a public repo expands the attack surface of the home lab.

## Decision

While the remote is public, committed inventory uses **roles and aliases only**. IPs, MACs, serial numbers, and SSH URIs go in gitignored `*.local.yaml` overlays. Adjacent systems may be named at a high level (for example "Clarion lab VMs on a private /24") without listing addresses.

If D-001 makes the repository private, a later ADR may allow deeper committed inventory. Until then this boundary holds.

## Consequences

- Phase 1 can still collect facts; it must store the sensitive ones locally unless visibility changes.
- Security docs may describe findings (Ollama on `*:11434`) without publishing a network map.
