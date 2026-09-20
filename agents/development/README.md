# Development agent

**Status:** Contract + policy + deterministic plan (`repo_read`, `git_status`). Studio worker can execute it. **Not deployed. Not an LLM.**

Workflow: work order → read repo → branch → bounded changes → checks → summary → human review → PR.

Must not: unrestricted filesystem, org-wide GitHub tokens, merge/push/deploy without approval.

Allowed tools in `policy.json` are names the harness understands. Privileged tools trip `awaiting_approval`.
