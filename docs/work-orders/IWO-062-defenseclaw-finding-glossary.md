# IWO-062 — DefenseClaw finding glossary

**Status:** In progress (unit tests; Findings pane not checked in the browser)  
**Priority:** P2  
**Effort:** M  
**Owner:** human (operator)  
**Feature:** [FEAT-014](../features/FEAT-014-defenseclaw-operator-governance.md)  
**Services / Areas:** platform, docs

## Problem

The Security **Findings** list shows a title, a rule id, a count, and a short match token. It does not say what the rule is for or what a block meant.

Observed on the Air, 2026-09-25, from `~/.defenseclaw/audit.db` (read-only). Counts move while the gateway is running; they are a snapshot, not a quota.

- About 41,500 `audit_events`. More than half are `correlation.relationship.changed`.
- 908 `scan_findings`. The repeated security titles are `CMD-ENV-DUMP` (evidence text `env`, description empty), `CMD-PYTHON-C`, `COG-AGENTS-MD`, and `COG-MEMORY`. Remediation is filled on 2 rows. `decision_path` is empty.
- About 490 info rows are AI-BOM inventory (`aibom-claw.finding.*`), repeated on each scan.
- Hook rows store `defenseclaw.guardrail.rule_ids` and `defenseclaw.guardrail.reason`. On non-allow hooks the reason starts with `matched` and is 36–173 characters. The indexed columns `tool_name`, `target`, `finding_id`, and `scan_id` are empty. `would_block` is false on rows whose effective action is `block`.
- The installed rule pack (`defenseclaw/_data/policies/guardrail/*/rules/*.yaml`) has id, title, severity, and the match pattern. It has no prose description. Copying those files into Git would copy the patterns. Opening them in an agent session trips the same hooks.

IWO-061 already replaces the raw `finding.observed` alert line with the finding title. This slice adds the missing sentence.

## Decision Context

- Chosen approach: A glossary in this repo, keyed by `rule_id`, written as operator prose. The mini attaches that prose when it renders a report. The Air adds a collapsed **Decisions** list for `block` and `confirm` only: action, rule id, hook phase, severity, count, latest timestamp. `defenseclaw.guardrail.reason` stays on the Air.
- Alternatives rejected: Sending every audit row to a model. Wrapping `defenseclaw setup`, `mcp`, or `tool` as agent tools. Copying the rule pack or `audit.db`.
- Assumptions: IWO-061’s report shape stays (`findings.by_title`, `findings.recent`, secret refusal, 15-minute stale mark). A decision can carry more than one rule id; the card lists each id that has a glossary entry.
- Open decisions:
  - `alert` hook rows (on the order of 90 in the snapshot, mostly the same rule ids as findings) are omitted here. Accept this IWO to keep that omission, or say so before acceptance if they should be a third list.
  - Glossary sentences ship in the implementation PR. The human verification pass includes reading every CRITICAL and HIGH entry.

## What To Build / Fix

Glossary file loaded by the platform (YAML or a small Python table under `platform/src/ai_lab_platform/`). Each entry:

- `rule_id`
- one sentence, `meaning` — what the rule is for
- one sentence, `usual_case` — the common lab case (reading `AGENTS.md`, `python -c`, a command that prints `env`)
- `class`: `enforcement` or `inventory`

Cover at least the rule ids seen on the Air in the 2026-09-25 snapshot:

`CMD-ENV-DUMP`, `CMD-PYTHON-C`, `CMD-EVAL`, `CMD-RM-RF`, `CMD-PIPE-CURL`, `CMD-NETCAT-LISTEN`, `CMD-SOCAT-EXEC`, `COG-AGENTS-MD`, `COG-MEMORY`, `COG-IDENTITY`, `COG-CLAUDE-MD`, `COG-SOUL`, `COG-TOOLS-MD`, `PATH-SSH-DIR`, `PATH-SSH-KEY`, `PATH-ENV-FILE`, `CG-NET-001`, `CG-PATH-001`, `CG-EXEC-001`, `CG-SQL-001`, `CORR-DESTRUCTIVE-FLOW`, `CORR-ESCALATION-CHAIN`, `ENT-CC-VISA`.

One shared inventory entry for any `rule_id` that starts with `aibom-`. Unknown ids use a fixed fallback: “No explanation for this rule yet.” plus the id. Do not invent a meaning.

`read_finding_summary` stays facts from `scan_findings`. `posture_view` (or the equivalent view helper) attaches `meaning`, `usual_case`, and `class` by rule id so a glossary edit shows up without a new Air push.

Air report gains `decisions`, built in `defenseclaw_report.py` and passed through `scripts/defenseclaw-report.sh`:

- Read `audit_events` where `event_name` is `hook_decision` and `defenseclaw.guardrail.effective_action` is `block` or `confirm`.
- Emit aggregates only: `action`, `rule`, `hook` (`defenseclaw.hook.event`), `severity`, `count`, `latest`.
- Drop `reason`, command text, paths, session ids, and the rest of the payload.
- Run the same secret refusal as the rest of the report.

Findings pane in `platform/src/ai_lab_platform/web/agents.html`:

- Selecting a rollup row shows `meaning` and `usual_case` above the existing when / where / matched table.
- Rows with `class: inventory` collapse to one Inventory card (count of those rows, not one card per `Skills (1)` / `Plugins (0)` line).
- A Decisions block lists the aggregates. Each row uses the same glossary. Empty decisions say that this report has no blocks or confirms.

Docs to touch when implementing, not in this draft: one sentence on the DefenseClaw section of `docs/architecture/security-plane.md`, and the FEAT-014 implementation-status row.

## Expected Change Surface

- Expected: `platform/src/ai_lab_platform/defenseclaw_report.py`, new glossary module or data file, `scripts/defenseclaw-report.sh`, `platform/src/ai_lab_platform/web/agents.html`, `tests/test_defenseclaw_report.py`.
- Tests: glossary hit and fallback; inventory collapse; a decision aggregate has no `reason` and no payload; a secret-like decision field is refused; existing posture secret tests still pass.
- Docs/status: this file’s Closeout, `docs/features/index.md`, `docs/work-orders/README.md`, `docs/architecture/security-plane.md`, FEAT-014 status row.

## Out Of Scope

- A model that explains one card on demand. File that as a follow-on after these cards are stable. It gets the redacted card only, and it does not allow, block, or edit policy.
- `alert` hook rows, `correlation.relationship.changed`, and tool-invocation telemetry.
- Changing DefenseClaw configuration, hooks, or allow / block lists.
- Copying `config.yaml`, `device.key`, `audit.db`, or the rule-pack YAML.
- API gateway and Antares repo choice (ADR 0040).

## Do NOT Change

- DefenseClaw stays on the Air. The mini stores the posted summary only.
- IWO-061 secret refusal, home-path stripping, and the 15-minute stale mark.
- `defenseclaw-report.sh` stays print-only unless the operator passes `--apply`. This IWO does not authorize `--apply`.
- No listener bind change, no lab compose on the Air, no runtime work-order row.
- Glossary text must not include match patterns, sample exploits, or command lines copied from the rule pack.

## Acceptance Criteria

1. A fixture finding with rule `CMD-ENV-DUMP` renders a non-empty `meaning` that does not contain a regex or a shell pipeline.
2. An unknown rule id renders the fallback sentence and the id.
3. Seven `aibom-claw.finding.*` rows in one report become one Inventory card.
4. A fixture hook payload whose reason contains a command string produces a `decisions` entry with `action`, `rule`, `hook`, `severity`, `count`, and `latest` only. The posted JSON has no `reason` field.
5. A secret-like value in a decision field is refused, same as the rest of the report.
6. `./scripts/validate-repo.sh` and `python3 -m unittest discover -s tests -v` pass.
7. On the Security Findings pane, selecting a known rule shows the two glossary sentences and the existing match table. Decisions with no rows show the empty line.

## Validation Plan

- Automated: extend `tests/test_defenseclaw_report.py` for the glossary join, inventory collapse, decision aggregate, and secret refusal. No live `audit.db` in tests.
- Manual: `./scripts/defenseclaw-report.sh` on the Air (print only). Confirm the JSON decisions omit `reason`. Open **Security** after a report is stored and read one CRITICAL or HIGH card. `--apply` only if the operator authorizes it separately; IWO-061 still notes the Air may lack `~/.ai-lab/api.token`.
- Evidence to include: unit-test names, and either the print-only JSON keys for `decisions[0]` or a note that the Air script was not run.

## AI Lab gates (required)

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none
- **May run on Air?** Yes — `defenseclaw-report.sh` read-only print. Lab compose on the Air is forbidden.

## Execution

- **Branch:** `iwo/062-defenseclaw-finding-glossary`
- **Risk tier:** P2
- **Pre-PR / pre-merge gate:** `./scripts/validate-repo.sh` and `python3 -m unittest discover -s tests -v`
- **Depends on:** IWO-061 (report and Findings pane). Implement against that shape while IWO-061 is in progress; do not wait for Air `--apply`.
- **Human verification required:** Yes — Findings pane, and a read of the CRITICAL and HIGH glossary sentences.
- **Reviewer / approver:** human (operator)
- **Project status record:** `docs/features/index.md` and this file
- **Other status surfaces:** FEAT-014, `docs/work-orders/README.md`

## Closeout

- Verification evidence: `python3 -m unittest tests.test_defenseclaw_report -v` (10 tests). Air `defenseclaw-report.sh` print was not run in this pass.
- Follow-ons filed: the operator asked for the outcome, so this slice now includes recent block episodes and `POST /v1/security/explain`. The model sees the card only. It is not a separate studio agent.
- Residual risks: glossary sentences for CRITICAL and HIGH rules still need a human read. The Findings pane was not opened in a browser.
- Docs/status updated: this file, `docs/features/index.md`, `docs/work-orders/README.md`, FEAT-014, `docs/architecture/security-plane.md`
- Status surfaces reconciled: yes
- Summary metadata reviewed: yes
- Planning-only change? No
- Host deploy performed? No
