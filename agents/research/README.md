# Research agent

**Status:** Contract + policy + deterministic plan (`write_report_artifact` only). Studio worker can execute it. **Not deployed. Not an LLM.**

Workflow: objective → authorized sources → citations → separate evidence from inference → report → store findings → record uncertainty.

Must not fabricate citations. Until an HTTP allowlist exists, the local plan writes a limitations report and does not fetch. Empty retrieval must not become a hallucinated bibliography.
