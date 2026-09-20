# Agents

Three initial categories. None of these is autonomous or production-ready. A **deterministic local plan** exists for each and is executed by the laptop worker and the Studio worker; there is no LLM loop and nothing is deployed.

| Agent | Policy | Isolation | Status |
|-------|--------|-----------|--------|
| [development](development/README.md) | bounded git | workspace allowlist | Scaffolded on harness |
| [research](research/README.md) | sourced reports | HTTP allowlist | Scaffolded |
| [lab-operations](lab-operations/README.md) | **read-only** | health endpoints | Scaffolded |

Catalog: [catalog.md](catalog.md)
