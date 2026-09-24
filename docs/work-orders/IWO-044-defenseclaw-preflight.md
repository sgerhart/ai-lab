# IWO-044 — DefenseClaw preflight (Air, read-only)

**Status:** Complete  
**Priority:** P2  
**Effort:** S  
**Owner:** human (operator)  
**Feature:** [FEAT-014](../features/FEAT-014-defenseclaw-operator-governance.md)  
**Risk tier:** P2  

## Problem

DefenseClaw is already on the Air, but the lab had no checked-in way to verify
status without improvising shell and without risking a live `setup` mutate.

## What shipped

- `scripts/defenseclaw-preflight.sh` — dry-run / read-only by default
- FEAT-014 + inventory note
- Documents that Cursor connector setup is a **separate** authorize step (IWO-045)

## Out Of Scope

- `defenseclaw setup cursor` / gateway restart
- Scanning or allowlisting MCP servers

## Acceptance Criteria

1. Script exits 0 when CLI is present and prints mode/connector/sidecar summary.
2. Does not write under `~/.defenseclaw` or `~/.cursor`.
3. No secrets printed.

## AI Lab gates

- **Host deploy / mutate authorized by this IWO alone?** **No**
- **May run on Air?** Yes (read-only)

## Closeout

- Verification evidence: script `--help` + local run on Air
- Follow-ons: IWO-045 Cursor Add (deploy-gated)
- Host deploy performed? No
