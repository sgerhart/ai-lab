# IWO-056 — Read-only Coding Assistant

**Status:** Complete (unit tests; no writes, no host mutate)  
**Priority:** P1  
**Effort:** M  
**Owner:** human (operator)  
**Feature:** [FEAT-016](../features/FEAT-016-local-coding-models-and-assistant.md)  
**Services / Areas:** platform, agents

## Problem

IWO-055 can select a coding model. The harness still had no read-only coding identity: `development` lists write tools that are not implemented, and `repo_read` could not take a relative path.

## What landed

- Agent `coding-assistant` with a read-only policy: `repo_read`, `repo_search`, `git_status`, `git_diff`.
- Path checks stay inside `workspace_root` / `bounded_scope`. `../` is denied.
- Write names (`repo_write_bounded`, `git_commit`, `run_tests`, push, deploy) are denied when not allowlisted.
- Agents UI persona list includes `coding-assistant`.
- Fixture: `tests/fixtures/coding-sample/` (not Clarion).

## Out of scope

Worktrees, patches, test execution, pull requests (IWO-058). Model pulls.

## Acceptance

1. Policy loads and is `read_only`.
2. Search and diff work on a fixture workspace.
3. Escaping the workspace raises `PathEscape`.
4. Write tool names are denied.
5. `python3 -m unittest tests.test_coding_assistant` passes.

## AI Lab gates

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized?** No
- **Privileged tools expected?** none
- **May run on Air?** Yes (tests)
- **Usage-billed API?** No
- **Model pull?** No
