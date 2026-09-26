# IWO-061 — DefenseClaw summary on Security

**Status:** Complete (Air posts every 10 minutes; the card stays ahead of the 15-minute stale mark)  
**Priority:** P2  
**Feature:** [FEAT-014](../features/FEAT-014-defenseclaw-operator-governance.md)  
**Decision:** [ADR 0040](../decisions/0040-security-plane-gateway-and-antares.md)

## What this slice does

The Air builds a DefenseClaw report: versions, the agents it is watching, the operator config (secret values withheld), guardrail, and finding titles from the audit database. `./scripts/defenseclaw-report.sh` prints that JSON. `--apply` posts it to `POST /v1/security/posture` on the mini. The DefenseClaw badge on **Security** opens that detail and marks it stale after 15 minutes. The raw `alerts` table only says `finding.observed`; the page uses the finding title and rule instead.

The summary refuses secret-like keys and values. `config.yaml`, `device.key`, and `audit.db` are not copied.

## Not in this slice

Changing DefenseClaw configuration from the page, the API gateway, or choosing a Clarion snapshot for Antares.

## Acceptance

- [x] A report with counts round-trips through the authenticated API
- [x] A secret-like value is refused
- [x] Operator report stored on the mini. On 2026-09-26 the Air `--apply` posted with the existing lab token file, and `com.ai-lab.defenseclaw-report` repeats that post every 10 minutes. The operator reloaded Security and the badge was current.
