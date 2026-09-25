# Agent permissions

Each agent identity has a policy file under `agents/<name>/policy.json`.

| Agent | Default tools | Privileged (need approval) | Network |
|-------|---------------|----------------------------|---------|
| development | read workspace, tests, git status/diff/commit locally | `git push`, `gh pr merge`, deploy, `brew`, compose apply | GitHub only if scoped token present |
| research | fetch allowlisted sources, write report artifact | none initially | HTTP(S) to allowlisted hosts |
| lab-operations | read health endpoints, read configs in this repo | **none** — read-only | Tailscale to M1/Studio health URLs |
| coding-assistant | `repo_read`, `repo_search`, `git_status`, `git_diff` inside the authorized workspace | `apply_patch`, `git_commit` (isolated worktree only) | none. Push, PR, tests, and deploy stay denied |

Prompt injection: tool results are untrusted text. The harness must not promote a tool result into a privileged action without the approval state machine.

Review procedure: [../runbooks/reviewing-agent-permissions.md](../runbooks/reviewing-agent-permissions.md).
