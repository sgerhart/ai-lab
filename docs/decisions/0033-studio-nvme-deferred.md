# ADR 0033 — Studio Thunderbolt NVMe is out of initial setup

- **Status:** Accepted
- **Date:** 2026-09-21
- **Supersedes:** open decision D-018

## Context

ADR 0010 left model paths configurable for a future Thunderbolt NVMe. The owner stated the drive is coming and is **not** part of initial setup.

## Decision

Initial Studio disk is the internal 1 TB SSD. Do not require NVMe in bootstrap, Brewfile, or first `ollama pull`. When the drive exists, a new ADR will set `AI_LAB_MODEL_ROOT` (and related paths).

## Consequences

- `hosts/studio` runbook: NVMe is future, not a blocker.
- Paths stay overridable via environment / overlay so the later ADR does not require a layout rewrite.
