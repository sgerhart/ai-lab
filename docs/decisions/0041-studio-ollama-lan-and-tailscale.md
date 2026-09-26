# ADR 0041 — Studio Ollama listens on the LAN and the tailnet

- **Status:** Accepted
- **Date:** 2026-09-25
- **Supersedes:** the Studio bind sentence in [ADR 0019](0019-ollama-initial-inference.md) and [ADR 0029](0029-air-ollama-bind-accepted.md)

## Context

Studio Ollama was started with `OLLAMA_HOST` set to the Studio Tailscale address only. Ollama accepts one bind address. That choice left loopback and the home LAN closed, so a machine on the local network could not call `:11434`.

## Decision

`com.ai-lab.ollama` on `mac-studio` uses `OLLAMA_HOST=0.0.0.0:11434`. One process then answers on loopback, the Studio LAN interface, and Tailscale.

- Tailnet clients keep `http://mac-studio:11434`.
- A machine on the same LAN as the Studio uses that host’s local address, port 11434.
- Do not forward port 11434 on the router. Ollama has no authentication.

The Air listener stays the accepted workstation risk in ADR 0029. Lab inference remains Studio Ollama.

## Consequences

Anyone who can route to the Studio on the LAN can call the API. Applied on the Studio LaunchAgent on 2026-09-25. `http://mac-studio:11434` and loopback on the Studio both answered after the restart.
