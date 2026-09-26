# IWO-061 — DefenseClaw summary on Security

**Status:** In progress (unit tests; Air has not been told to `--apply`)  
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
- [x] Operator report stored on the mini (2026-09-25, via the lab API). The Air script `--apply` still needs `~/.ai-lab/api.token` on the Air; this host does not have that file yet.
