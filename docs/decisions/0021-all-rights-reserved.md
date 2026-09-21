# ADR 0021 — All-rights-reserved until an SPDX license is chosen

- **Status:** Accepted
- **Date:** 2026-09-21
- **Supersedes:** open decision D-003 for the *current* tree

## Context

`LICENSE` is already all-rights-reserved. A public SPDX license (MIT, Apache-2.0) would be a separate product decision. The GitHub remote is public (F-002 / D-001 still open).

## Decision

Keep **all rights reserved**. Do not add an MIT/Apache header. Agents must not relicense the tree. D-001 (public vs private) is independent: visibility does not grant a license.

## Consequences

- Copyright holder: Steven Gerhart, 2026.
- A later SPDX license requires a new ADR and a `LICENSE` replacement.
