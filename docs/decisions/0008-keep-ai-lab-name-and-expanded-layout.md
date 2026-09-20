# ADR 0008 — Keep `ai-lab` and expand the layout

- **Status:** Accepted (supersedes ADR 0004)
- **Date:** 2026-09-20
- **Phase:** 0 (revised)

## Context

The original layout (`docs/`, `hosts/`, `infrastructure/`, `agents/`, `models/`, `scripts/`, `tests/`) was a documentation skeleton. The platform now includes a three-host lab, an agent harness, and a model laboratory. Renaming the GitHub repository would break the already-created remote `sgerhart/ai-lab`.

## Decision

Keep the repository name **`ai-lab`**. Expand the tree with `platform/`, `.github/`, host directories `studio`, `m1-mini`, `m3-air`, and a split `docs/architecture/` tree. Do not create `ai-infrastructure/` or rename to `agent-lab` / `ai-factory` / `dentro-ai`.

Repository *implementation* of later phases is allowed. Host *deployment* remains phase-gated and unauthorized by default (ADR 0006 still applies to machines).

## Consequences

- `docs/architecture.md` and `docs/security.md` become directories (macOS cannot host both a file and a directory of the same name).
- `hosts/mac-workstation/` remains as a pointer to `hosts/m3-air/` so prior Phase 0 text is not silently deleted.
- Validators require the expanded paths.

## Alternatives considered

- Nested `ai-infrastructure/` project — rejected; splits the source of truth.
- Rename repository — rejected; remote already exists.
