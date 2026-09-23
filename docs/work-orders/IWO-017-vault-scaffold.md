# IWO-017 — Vault compose scaffold and provider secret names

**Status:** Complete  
**Priority:** P1  
**Effort:** S  
**Owner:** human + agent  
**Feature:** [FEAT-012](../features/FEAT-012-lab-site-and-secret-vault.md)  
**Services / Areas:** infrastructure, docs

## Problem

FEAT-011 cloud providers and Studio Jupyter open-token need a durable secret
home on the mini. ADR 0039 chooses HashiCorp Vault; Git must only hold names.

## What To Build / Fix

- Optional Compose `vault` service under profile `vault`
- `infrastructure/secrets/` name list for providers + jupyter token
- Example env placeholders only
- Runbook stub for init (no live unseal in this IWO)

## Out Of Scope

- `compose --profile vault up` on a live mini (separate host auth)
- Writing real API keys
- Router reading Vault at runtime (follow-on IWO)

## Acceptance Criteria

1. `docker compose … --profile vault config` succeeds with example env
2. No real secrets in tree
3. ADR 0039 linked from secrets README and features index

## AI Lab gates

- **Host deploy authorized by this IWO alone?** **No**
