# IWO-011 — Verify and configure Studio Tailscale (host gate)

**Status:** Draft  
**Priority:** P1  
**Effort:** S  
**Feature:** [FEAT-006](../features/FEAT-006-studio-jupyterlab.md), [FEAT-003](../features/FEAT-003-studio-worker-and-models.md)  
**Risk tier:** P0 (host network)

## Problem

Studio is not on the tailnet; Jupyter and Studio Ollama cannot proceed.

## What To Build / Fix

Runbook + checklist only in Git until owner authorizes host changes. After
authorization: join Tailscale as `mac-studio`, verify SSH from Air.

## AI Lab gates

- **Host deploy authorized by this IWO alone?** No — requires explicit conversation auth
- Do not run `--apply` in the planning PR

## Acceptance Criteria

1. Docs list exact authorized steps
2. After auth: `mac-studio` reachable from Air
