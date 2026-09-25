# IWO-058 — Isolated coding worktree and exact-action writes

**Status:** Complete (unit; Studio can prepare an isolated copy)  
**Priority:** P1  
**Effort:** M  
**Feature:** [FEAT-016](../features/FEAT-016-local-coding-models-and-assistant.md)  
**Services / Areas:** platform, agents

## What landed

- `prepare_worktree` creates a detached git worktree outside the source checkout and writes an isolation marker.
- `apply_patch` and `git_commit` are privileged. They refuse the primary checkout even if approved.
- `git_push` stays denied.
- `coding-assistant` policy lists those two tools as privileged only.

## Not in this slice

Test execution, pull requests, or Clarion. Push stays denied.

Studio can prepare a separate copy from a Coding agent and start a run. Approving a patch or commit applies only to that copy. The button labels are part of the screen the operator has not accepted (D-019).

## Gates

- **Host mutate?** No
- **Privileged tools?** `apply_patch`, `git_commit` (approval-bound; isolated worktree only)
- **Push / deploy?** No
