# IWO-102 — Modern Agent Harness and Second Brain Architecture

**Status:** Complete (unit; not deployed)
**Priority:** P1
**Effort:** M
**Owner:** Steven Gerhart
**Feature:** [FEAT-010](../features/FEAT-010-mini-personal-agent-loop.md), [FEAT-017](../features/FEAT-017-agent-operating-studio.md)
**Services / Areas:** platform (agent harness, tools, memory, research)
**Risk tier:** P2

## Problem

The previous agent harness relied on brittle regex string matching (`TOOL` / `FINAL`), hardcoded agent branches (`if policy.id == "personal"`), rigid string truncation, and silent error fallbacks where unparsed tool calls were treated as final answers. Furthermore, the agent loop lacked a clean integration for multi-source web research, structured reports, second-brain memory vault grounding, and reasoning model support.

## Decision Context

- **Chosen approach**:
  1. Refactor `agent_loop.py` to support robust structured tool calling, reasoning/thought tag extraction (`<think>...</think>`), and self-correcting error feedback.
  2. Decouple agent-specific logic from the core loop: use declarative policy capabilities for tool registration, repeatability rules, and memory context injection.
  3. Integrate Second Brain capabilities: multi-source research (`research_pages`), deep web lookup, structured markdown reports (`report_write`, `report_read`, `report_list`), and memory vault hooks.
  4. Ensure 100% backward compatibility with existing tests and policies while enabling advanced agent autonomy.
- **Alternatives rejected**: Rewriting the entire stack in an external framework without preserving security plane invariants (rejected: violates ADR 0017, ADR 0020, and AGENTS.md).
- **Assumptions**: Local Ollama or cloud backend models will receive standardized structured prompts and return cleanly parsed tool invocations or final synthesis.

## What To Build / Fix

1. `platform/src/ai_lab_platform/agent_loop.py`: Upgraded tool parsing, thinking-block handling, decoupled policy hooks, self-correcting error observations, token-aware context windowing.
2. `platform/src/ai_lab_platform/tool_runtime.py` & `tool_catalog.py`: Support for second-brain tools, research reports, and clean capability delegation.
3. `tests/test_revised_agent_harness.py`: Comprehensive test suite verifying structured parsing, reasoning tag isolation, error recovery, memory vault injection, and research reports.
4. Docs and work order tracking.

## Expected Change Surface

- Expected: `platform/src/ai_lab_platform/agent_loop.py`, `platform/src/ai_lab_platform/tool_runtime.py`, `platform/src/ai_lab_platform/research_reports.py`, `docs/work-orders/IWO-102-modern-agent-harness-and-second-brain.md`
- Tests: `tests/test_revised_agent_harness.py`, `tests/test_agent_loop.py`
- Docs/status: this file, `docs/work-orders/README.md`

## Out Of Scope

- Modifying hypervisor security plane VM execution (FEAT-019).
- Modifying live remote deployments or mutating host files outside the repository.

## Do NOT Change

- Security plane isolation guarantees (ADR 0040, ADR 0043).
- Authorization requirements for privileged tools (ADR 0018).
- Least privilege principle.

## Acceptance Criteria

1. Structured tool parsing correctly extracts JSON tool calls, legacy `TOOL <name> {args}` formats, and handles models with `<think>...</think>` blocks without premature termination.
2. Failed tool invocations feed error observations back to the model to allow self-correction rather than prematurely terminating as `FINAL`.
3. Agent policy context, memory vault briefs, and allowed tools are provided dynamically via policy abstractions rather than hardcoded `if policy.id == "personal"` checks.
4. Full second-brain tool capabilities (memory vault, web research, report authoring) are accessible to authorized agents.
5. All 330 unit tests pass, including the new comprehensive harness tests.
6. `./scripts/preflight.sh && ./scripts/validate-repo.sh && ./tests/test_structure.sh && python3 -m unittest discover -s tests -v` succeeds.

## Validation Plan

- Automated: `python3 -m unittest discover -s tests -v`
- Structural: `./scripts/validate-repo.sh && ./tests/test_structure.sh`
- Evidence to include: Test suite execution summary.

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none
- **May run on Air?** Yes for unit tests. Lab compose on Air is forbidden.

## Execution

- **Branch:** working tree
- **Risk tier:** P2
- **Pre-PR / pre-merge gate:** `./scripts/validate-repo.sh && python3 -m unittest discover -s tests -v`
- **Depends on:** IWO-099, IWO-100, IWO-101
- **Human verification required:** No
- **Reviewer / approver:** Steven Gerhart
- **Project status record:** this file and `docs/work-orders/README.md`
- **Other status surfaces:** FEAT-010, FEAT-017

## Closeout

- Verification evidence: `python3 -m unittest discover -s tests -v` — Ran 330 tests in 6.54s, OK (skipped=2). Validation scripts (`preflight.sh`, `validate-repo.sh`, `test_structure.sh`) passed.
- Follow-ons filed: none
- Residual risks: none
- Docs/status updated: yes
- Status surfaces reconciled: yes
- Summary metadata reviewed: yes
- Planning-only change? No
- Host deploy performed? No
