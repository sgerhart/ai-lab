# Lab operations agent

**Status:** Contract + policy + deterministic plan (`health_read`, `compose_ps_read`). **Read-only.** Studio worker can execute it. **Not deployed. Not an LLM.**

Inspect approved systems, diagnostics, telemetry, health, config drift, troubleshooting summaries.

Must not change network, firewall, identities, certificates, or production systems. No write tools in `policy.json`.
