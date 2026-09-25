# Coding Assistant

**Status:** Read tools are live. Writes run only in an isolated git worktree after approval of that exact action (not on the primary checkout). Push is denied. Not autonomous.

Allowed without a gate: `repo_read`, `repo_search`, `git_status`, `git_diff` inside the authorized workspace.

After you approve the exact call: `apply_patch`, `git_commit`. Both refuse unless the workspace is a disposable `git worktree` marked by the harness. The primary clone is never patched.

Still denied: `git_push`, pull requests, deploy, and running tests.

Do not point the first runs at Clarion.
