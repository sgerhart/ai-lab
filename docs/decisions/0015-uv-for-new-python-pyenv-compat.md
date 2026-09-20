# ADR 0015 — `uv` for new Python; retain `pyenv` compatibility

- **Status:** Accepted
- **Date:** 2026-09-20

## Context

The operator already uses `pyenv` (this workspace has `uv` on the pyenv shim path and Python 3.11.9). Existing product repos cannot be assumed to migrate.

## Decision

**New** lab projects (platform, eval, training, infra helpers) use:

- Homebrew for system tools
- `uv` for Python versions, venvs, resolution, and lockfiles
- Isolated env per project
- Checked-in `pyproject.toml` and `uv.lock` where `uv lock` has been run
- No global `pip install`

Existing projects may keep `pyenv`. Do not rewrite them from this repository.

Separate uv projects: `platform/`, `models/training/`, `models/evaluations/`, `models/mlx/`.

## Consequences

- Bootstrap installs `uv` via Homebrew where possible; if `uv` already exists via pyenv, preflight accepts either.
- CI uses `astral-sh/setup-uv` and does not need pyenv.

## Alternatives considered

- Force-migrate everything to uv — rejected.
- Conda as default — extra weight on 16 GB M1; not default.
