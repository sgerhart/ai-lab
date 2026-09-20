# ADR 0002 — Git root is `ai-lab`

- **Status:** Accepted
- **Date:** 2026-09-19
- **Phase:** 0

## Context

GitHub repository `sgerhart/ai-lab` was created on 2026-09-19. The first commit (`a5aff94`, message `first commit`) was made with Git metadata in `/workspace/github/sgerhart` — the parent directory that also holds Clarion, Oryntra, VolexSwarm, and other projects. The documented root, and the Cursor workspace, is `/workspace/github/sgerhart/ai-lab`, which had no `.git` directory.

Creating a second repository would split history from the existing remote. Leaving Git in the parent would keep a public remote attached to a directory tree full of unrelated projects.

## Decision

Relocate the existing `.git` directory and stub `README.md` into `/workspace/github/sgerhart/ai-lab`. Do not run `git init` again. Do not create `ai-lab/ai-infrastructure/`. Do not commit or push as part of this decision.

## Consequences

- `git rev-parse --show-toplevel` in this workspace is `.../ai-lab`.
- The parent workspace is no longer a Git work tree.
- History (`a5aff94`) and `origin` (`git@github.com:sgerhart/ai-lab.git`) are preserved.
- Future `git add .` from the lab root cannot stage sibling product repos.
