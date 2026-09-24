# IWO-028 — Deep research mode (Studio + frontier)

**Status:** Complete (gated)  
**Priority:** P1  
**Effort:** S  
**Feature:** [FEAT-013](../features/FEAT-013-personal-agent-studio.md), [FEAT-011](../features/FEAT-011-frontier-model-access.md)  
**Risk tier:** P1

## Problem

Need an explicit path to foundational models for heavy synthesis without making
them the default.

## What shipped

- `deep_research` flag on chat message + stream endpoints
- When true: requires `usage_billed_authorized` + Anthropic or OpenAI key;
  routes to frontier backend (IWO-021)
- UI Deep research toggle with billing-visible mode note
- Studio remains default when toggle off

## Closeout

- Evidence: control_app deep_research gates; no live $ in tests
- Live chargeable call: only when operator authorizes on `/secrets`
