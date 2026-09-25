# ADR 0040 — Security plane: API gateway, DefenseClaw, Antares

- **Status:** Accepted (direction). Nothing in this ADR is deployed.
- **Date:** 2026-09-25
- **Related:** ADR 0007, 0025, 0037, 0038, 0039; FEAT-011, FEAT-014, FEAT-015

## Context

The operator wants AI Lab to be the security testing ground for the lab: one
**Security** view on the mini, DefenseClaw on the Air, and a place to inspect
software (including adjacent repos such as Clarion). Foundation-model API calls
from the mini and the Air should pass through one security gateway on the
tailnet. Studio local inference should stay on the existing mini-to-Studio path.

DefenseClaw is already running on the Air (CLI and Textual dashboard). Its
audit and config stay in `~/.defenseclaw`. The Studio **Security** page today
only links to Antares. Antares-1B is live as a vulnerability-localization job
on the Studio, not as a general scanner.

## Decision

### Three tools, three jobs

| Tool | Where it runs | What it is for |
|------|----------------|----------------|
| DefenseClaw | `mac-air` | IDE and agent governance: connectors, scans, alerts, masked configuration |
| API gateway | Tailnet host, **default `mac-mini`** | The only egress for `usage_billed_api` calls from the mini and the Air |
| Antares | `mac-studio` | Localize a stated weakness class in a read-only repo snapshot |

The lab **Security** page on the mini is the console. DefenseClaw has no web
UI. `defenseclaw tui` stays a terminal on the Air.

### API gateway

- Local Studio Ollama and MLX stay on `STUDIO_OLLAMA_URL`. They do not pass through the gateway.
- OpenAI, Anthropic Console, and Gemini API calls from the mini harness and from the Air, when used as lab usage-billed calls, go to the gateway.
- The gateway holds the provider keys (ADR 0027 / 0039). Callers do not.
- Default host is the mini. A different tailnet device is allowed only if that device is the sole key holder. The hostname is recorded when the operator chooses it. Do not invent one here.
- The gateway records allow or deny. **Security** shows that record.
- ADR 0038 still applies: no silent fallback from local to billed, and subscription apps (Cursor, Claude) are not turned into a harness API.

### DefenseClaw

- The DefenseClaw process stays on the Air. This ADR does not move that gateway onto the mini (FEAT-014).
- The Air sends a summary to the mini: up or down, connectors and modes, recent activity, alerts, and the resolved configuration with secrets masked (`defenseclaw config show`).
- A confirmed change on **Security** is applied on the Air. The mini does not store `config.yaml`, `device.key`, or `audit.db`.
- A stale report is shown as stale.

### Antares

- Antares answers: given a weakness class, which files in this snapshot look relevant.
- The operator supplies a read-only copy of a repository on the Studio. That copy may be this lab, or an adjacent product repo such as Clarion.
- Clarion stays a separate product (ADR 0007, ADR 0025). A scan does not import that repo, start its stack, or reuse its Vault.
- A person reviews the result before any fix. Antares does not remediate and does not generate exploits.
- Job status and the reviewed result are visible from **Security** and from `/antares`.

## Consequences

- New work is an IWO under FEAT-014 (DefenseClaw summary and confirmed config changes) and FEAT-011 (gateway). Antares repo selection is a follow-on under FEAT-015.
- **Security** grows beyond the Antares badge. The badge remains the way to open a localization job.
- Deploy of the gateway, or any host change, still needs a separate human authorization.

## Alternatives considered

- Send local Studio traffic through the same gateway. Rejected. Those calls stay on the tailnet and are not foundation APIs.
- Run DefenseClaw’s process on the mini. Rejected for this ADR. Only its summary and confirmed actions cross to the mini.
- Treat Antares as a full application scanner for Clarion. Rejected. It localizes a stated weakness in a snapshot. Absorbing Clarion remains a different ADR.
